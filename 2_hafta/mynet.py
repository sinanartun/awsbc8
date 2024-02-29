import json
import requests
import re
from datetime import datetime
import boto3


def extract_data(raw_data,symbol):
    regex = re.compile(r'\[\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\s*\]')
    csv_data = 'date,high,low,close,volume\n'
    matches = regex.findall(raw_data)
    for match in matches:
        if match and match[0]:
            unix_time = float(match[0])
            date = unix_time
            data_array = match[1:]
            csv_data += f"{date},{','.join(data_array)}\n"
    if csv_data !='date,high,low,close,volume\n':
        with open(f'/tmp/{symbol}.csv', 'w') as f:
            f.write(csv_data)
        return csv_data
    else:
        raise ValueError('No data found')




def upload_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def lambda_handler(event, context):

    # symbol = int(event['queryStringParameters']['symbol'])
    # url = int(event['queryStringParameters']['url'])
    

    
    url = 'https://finans.mynet.com/borsa/hisseler/a1cap-a1-capital-yatirim/'
    response = requests.get(url)
    response.raise_for_status()  # Ensure we got a successful response

    csv_res = extract_data(response.text, 'A1CAP')

    # Write the content to a file (replace 'output.html' with your preferred file name)
    return {
        'statusCode': 200,
        'body': json.dumps(csv_res)
    }


