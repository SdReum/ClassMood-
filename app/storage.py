# import boto3
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# s3_client = boto3.client(
#     's3',
#     endpoint_url=os.getenv('S3_ENDPOINT_URL'),
#     aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
#     aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
#     region_name='us-east-1'
# )
#
# BUCKET = os.getenv('S3_BUCKET_NAME')