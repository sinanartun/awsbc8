import os
import boto3
from botocore.config import Config
import pprint
import json

os.environ['AWS_PROFILE'] = 'default'
my_config = Config(
    region_name = 'eu-north-1',
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

def create_vpc_and_subnets():
    global vpc_id, subnet_ids, region, az_list
    ec2 = boto3.resource('ec2', config=my_config)
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc.wait_until_available()
    vpc_id = vpc.id
    az_list = get_availability_zones()

    for i, az in enumerate(az_list, start=0):
        subnet = vpc.create_subnet(CidrBlock=f'10.0.{i}.0/24', AvailabilityZone=az)
        subnet_ids.append(subnet.id)

    create_internet_gateway_and_route_table()
    create_vpc_endpoint_for_s3()
    describe_vpc()
    write_vpc_data_to_json()


def get_availability_zones():
    global region, az_list
    ec2_client = boto3.client('ec2', config=my_config)
    response = ec2_client.describe_availability_zones()
    az_list = [az['ZoneName'] for az in response['AvailabilityZones']]
    return az_list

def describe_vpc():
    global vpc_id
    ec2_client = boto3.client('ec2', config=my_config)
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    pprint.pprint(response['Vpcs'][0])
    return response['Vpcs'][0] 

def create_internet_gateway_and_route_table():
    global ig_id, region, route_table_id, vpc_id, route_id, subnet_ids
    ec2 = boto3.resource('ec2', config=my_config)
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

def create_vpc_endpoint_for_s3():
    global vpc_id, route_table_id, region, vpce_s3_id
    ec2_client = boto3.client('ec2', config=my_config)
    response = ec2_client.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName=f'com.amazonaws.{my_config.region_name}.s3',
        RouteTableIds=[route_table_id],
        VpcEndpointType='Gateway',
        PrivateDnsEnabled=False
    )
    vpce_s3_id = response['VpcEndpoint']['VpcEndpointId']

def write_vpc_data_to_json():
    global vpc_id, ig_id, subnet_ids, az_list, route_table_id, route_id, vpce_s3_id
    vpc_data = {
        "vpc_id": vpc_id,
        "ig_id": ig_id,
        "subnet_ids": subnet_ids,
        "az_list": az_list,
        "route_table_id": route_table_id,
        "route_id": route_id,
        "vpce_s3_id": vpce_s3_id
    }

    with open(f'vpc_data_{vpc_id}.json', 'w') as f:
        json.dump(vpc_data, f, indent=4, sort_keys=True)

create_vpc_and_subnets()

