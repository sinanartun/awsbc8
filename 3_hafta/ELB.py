import os
import boto3
from botocore.config import Config
import pprint
import json
import ipaddress

os.environ['AWS_PROFILE'] = 'default'

sto_config = Config(
    region_name = 'eu-north-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

fra_config = Config(
    region_name = 'eu-central-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

irish_config = Config(
    region_name = 'eu-west-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)


vpc_id = None
ig_id = None
subnet_ids = []
az_list = []
route_table_id = None
route_id = None
vpce_s3_id = None

def create_vpc_and_subnets(cidr_block, region_config):
    global vpc_id, subnet_ids, region, az_list
    ec2 = boto3.resource('ec2', config=region_config)
    vpc = ec2.create_vpc(CidrBlock=cidr_block)
    vpc.wait_until_available()
    vpc_id = vpc.id
    az_list = get_availability_zones(region_config)

    # Create a network object from the VPC CIDR block
    network = ipaddress.ip_network(cidr_block)

    # Get a list of subnets for the network
    subnets = list(network.subnets(new_prefix=24))  # replace 24 with the desired subnet prefix length

    for i, az in enumerate(az_list, start=0):
        # Use the subnet CIDR block from the list of subnets
        sub_cidr = str(subnets[i])
        subnet = vpc.create_subnet(CidrBlock=sub_cidr, AvailabilityZone=az)
        subnet_ids.append(subnet.id)

    create_internet_gateway_and_route_table(region_config)
    create_vpc_endpoint_for_s3(region_config)
    describe_vpc(region_config)


def get_availability_zones(region_config):
    global az_list
    ec2_client = boto3.client('ec2', config=region_config)
    response = ec2_client.describe_availability_zones()
    az_list = [az['ZoneName'] for az in response['AvailabilityZones']]
    return az_list

def describe_vpc(region_config):
    global vpc_id
    ec2_client = boto3.client('ec2', config=region_config)
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    pprint.pprint(response['Vpcs'][0])
    return response['Vpcs'][0] 

def create_internet_gateway_and_route_table(region_config):
    global ig_id, region, route_table_id, vpc_id, route_id, subnet_ids
    ec2 = boto3.resource('ec2', config=region_config)
    ig = ec2.create_internet_gateway()
    ig_id = ig.id
    vpc = ec2.Vpc(vpc_id)
    vpc.attach_internet_gateway(InternetGatewayId=ig.id)
    route_table = vpc.create_route_table()
    route_table_id = route_table.id
    route = route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=ig.id
    )
    route_id = route.route_table_id
    for subnet_id in subnet_ids:
        route_table.associate_with_subnet(SubnetId=subnet_id)

def create_vpc_endpoint_for_s3(region_config):
    global vpc_id, route_table_id, region, vpce_s3_id
    ec2_client = boto3.client('ec2', config=region_config)
    response = ec2_client.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName=f'com.amazonaws.{region_config.region_name}.s3',
        RouteTableIds=[route_table_id],
        VpcEndpointType='Gateway',
        PrivateDnsEnabled=False
    )
    vpce_s3_id = response['VpcEndpoint']['VpcEndpointId']



# create_vpc_and_subnets('10.0.0.0/16', sto_config)
create_vpc_and_subnets('10.1.0.0/16', fra_config)

