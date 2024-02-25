import boto3
from botocore.exceptions import NoCredentialsError

def create_bucket(bucket_name, region=None):
    try:
        if region is None:
            s3_client = boto3.client('s3')

            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except NoCredentialsError:
        return False

def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name

    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print(response)
    except NoCredentialsError:
        return False
    return True

def download_file(bucket, object_name, file_name):
    s3 = boto3.resource('s3')
    try:
        s3.Bucket(bucket).download_file(object_name, file_name)
    except NoCredentialsError:
        return False
    return True


def list_objects_in_bucket(bucket_name):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name)
    for object in response['Contents']:
        print(object['Key'])

def get_session_token():
    sts_client = boto3.client('sts')
    response = sts_client.get_session_token()
    return response


def copy_object(src_bucket, src_key, dest_bucket, dest_key=None):
    s3_client = boto3.client('s3')
    if dest_key is None:
        dest_key = src_key
    copy_source = {
        'Bucket': src_bucket,
        'Key': src_key
    }
    s3_client.copy(copy_source, dest_bucket, dest_key)

# Usage
# copy_object('source-bucket-name', 'source-object-key', 'destination-bucket-name')

# print(get_session_token())

# create_bucket('1hafta', 'eu-north-1')

# upload_file('session.txt', '1hafta')
    

# list_objects_in_bucket('webinar001')    
    
# print(get_session_token())    
    
copy_object('webinar001', 'bin.zip', 'haydegidelum', 'bin2.zip')    