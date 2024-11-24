from botocore.exceptions import ClientError
import boto3
import config
import logging

class s3_client():

    global client, resource
    client = boto3.client('s3', region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id, 
                            aws_secret_access_key=config.aws_secret_access_key
                            )
    resource = boto3.resource('s3', region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id,
                            aws_secret_access_key=config.aws_secret_access_key
                            )

    def upload_file(self, file_name, object_name=None):
        try:
            if object_name is None:
                object_name = file_name
                response = client.upload_file(file_name, config.bucket_name, object_name)
                return response
        except ClientError as e:
            logging.error(e)
    
    def upload_fileobj(self, file, object_name=None):
        if object_name is None:
            object_name = file.filename
        try:
            response = client.upload_fileobj(file, config.bucket_name, object_name)
            return response
        except ClientError as e:
            logging.error(e)
    
    def download_file(self, object_name, file_name):
        try:
            response = client.download_file(config.bucket_name, object_name, file_name)
            return response
        except ClientError as e:
            logging.error(e)
    
    def download_fileobj(self, object_name, file_name):
        try:
            response = client.download_fileobj(config.bucket_name, object_name, file_name)
            return response
        except ClientError as e:
            logging.error(e)
    
    def delete_file(self, object_name):
        try:
            response = client.delete_object(Bucket=config.bucket_name, Key=object_name)
            return response
        except ClientError as e:
            logging.error(e)
    
    def create_url(self, object_name, expires_in=None, http_method=None):
        try:
            url = client.generate_presigned_url('get_object', 
                Params={'Bucket': config.bucket_name, 'Key': object_name}, 
                ExpiresIn=expires_in,
                HttpMethod=http_method
            )
            return url
        except ClientError as e:
            logging.error(e)