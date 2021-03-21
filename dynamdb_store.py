import boto3
import os


os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

# For a Boto3 client.
ddb = boto3.client('dynamodb', endpoint_url='http://localhost:8000')
response = ddb.list_tables()
table_names = response["TableNames"]




print(response)
#
# # For a Boto3 service resource
# ddb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
# print(list(ddb.tables.all()))
