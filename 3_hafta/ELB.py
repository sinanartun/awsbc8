import os
import boto3
from botocore.config import Config
import pprint
import json
import ipaddress

class VPCManager:
    def __init__(self, region_name):
        os.environ['AWS_PROFILE'] = 'default'
        self.config = Config(
            region_name = region_name,
            signature_version = 'v4',
            retries = {
                'max_attempts': 10,
                'mode': 'standard'
            }
        )
        self.ec2 = boto3.resource('ec2', config=self.config)
        self.ec2_client = boto3.client('ec2', config=self.config)
        self.vpc_id = None
        self.ig_id = None
        self.subnet_ids = []
        self.az_list = []
        self.route_table_id = None
        self.route_id = None
        self.vpce_s3_id = None

    def create_vpc(self, cidr_block):
        vpc = self.ec2.create_vpc(CidrBlock=cidr_block)
        vpc.wait_until_available()
        self.vpc_id = vpc.id

    def create_subnets(self, cidr_block):
        self.az_list = self.get_availability_zones()
        network = ipaddress.ip_network(cidr_block)
        subnets = list(network.subnets(new_prefix=24))  # replace 24 with the desired subnet prefix length
        for i, az in enumerate(self.az_list, start=0):
            sub_cidr = str(subnets[i])
            subnet = self.ec2.Vpc(self.vpc_id).create_subnet(CidrBlock=sub_cidr, AvailabilityZone=az)
            self.subnet_ids.append(subnet.id)

    def create_vpc_and_subnets(self, cidr_block):
        self.create_vpc(cidr_block)
        self.create_subnets(cidr_block)
        self.create_internet_gateway_and_route_table()
        self.create_vpc_endpoint_for_s3()
        self.describe_vpc()

    def get_availability_zones(self):
        response = self.ec2_client.describe_availability_zones()
        return [az['ZoneName'] for az in response['AvailabilityZones']]

    def describe_vpc(self):
        response = self.ec2_client.describe_vpcs(VpcIds=[self.vpc_id])
        pprint.pprint(response['Vpcs'][0])
        return response['Vpcs'][0] 

    def create_internet_gateway_and_route_table(self):
        ig = self.ec2.create_internet_gateway()
        self.ig_id = ig.id
        vpc = self.ec2.Vpc(self.vpc_id)
        vpc.attach_internet_gateway(InternetGatewayId=ig.id)
        route_table = vpc.create_route_table()
        self.route_table_id = route_table.id
        route = route_table.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=ig.id
        )
        self.route_id = route.route_table_id
        for subnet_id in self.subnet_ids:
            route_table.associate_with_subnet(SubnetId=subnet_id)

    def create_vpc_endpoint_for_s3(self):
        response = self.ec2_client.create_vpc_endpoint(
            VpcId=self.vpc_id,
            ServiceName=f'com.amazonaws.{self.config.region_name}.s3',
            RouteTableIds=[self.route_table_id],
            VpcEndpointType='Gateway',
            PrivateDnsEnabled=False
        )
        self.vpce_s3_id = response['VpcEndpoint']['VpcEndpointId']


# Usage:
vpc_manager = VPCManager('eu-north-1')
vpc_manager.create_vpc_and_subnets('10.0.0.0/16')

vpc_manager2 = VPCManager('eu-central-1')
vpc_manager2.create_vpc_and_subnets('10.1.0.0/16')