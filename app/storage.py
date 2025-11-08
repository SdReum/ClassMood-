"""Optional S3 storage configuration (commented out by default).

If you prefer storing uploads in cloud/object storage instead of the local
`uploads/` directory used in `app/media/routes.py`, you can:
- Install boto3 (add to requirements.txt)
- Fill in these environment variables in your .env:
  - S3_ENDPOINT_URL (e.g., https://s3.amazonaws.com or MinIO endpoint)
  - S3_ACCESS_KEY
  - S3_SECRET_KEY
  - S3_BUCKET_NAME
- Uncomment the code below and replace local file operations accordingly.
"""

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