import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("NEBULA_BLOCK_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("NEBULA_BLOCK_SECRET_KEY"),
    endpoint_url=os.environ.get("NEBULA_BLOCK_HOST"),
    region_name="us-east-1",
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)
# print(s3.list_buckets())
try:
    s3.upload_file(os.path.join("data", "files", "index.faiss"), "labor-law", "index.faiss")  
    s3.upload_file(os.path.join("data", "files", "chunks.json"), "labor-law", "chunks.json")  
except Exception as e:
    print(f"Error uploading files: {e}")