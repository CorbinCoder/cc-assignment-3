from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import boto3
import config
import logging

class db_client:
    global client, resource
    client = boto3.client('dynamodb', region_name=config.region_name,
                                aws_access_key_id=config.aws_access_key_id,
                                aws_secret_access_key=config.aws_secret_access_key
                                )
    resource = boto3.resource('dynamodb', region_name=config.region_name,
                                aws_access_key_id=config.aws_access_key_id,
                                aws_secret_access_key=config.aws_secret_access_key
                                )

    def create_table(self, table_name, key_schema, attribute_definitions, provisioned_throughput):
        print('Creating table: {}'.format(table_name))
        response = client.create_table(
            TableName=[table_name],
            KeySchema=[key_schema],
            AttributeDefinitions=[attribute_definitions],
            ProvisionedThroughput=[provisioned_throughput]
        )
        return response
    
    def put_item(self, table_name, item):
        table = resource.Table(table_name)
        response = table.put_item(Item=item)
        return response
    
    def get_item(self, table_name, key):
        try:
            table = resource.Table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logging.error(e)
        return None
    
    def update_item(self, table_name, key, update_expression, expression_attribute_values):
        response = client.update_item(
            TableName=table_name,
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return response
    
    def delete_item(self, table_name, pk_attribute, pk_value, st_attribute=None, st_value=None):
        table = resource.Table(table_name)
        if (st_attribute and st_value):
            response = table.delete_item(
                Key={
                    pk_attribute: pk_value,
                    st_attribute: st_value
                }
            )
        else:
            response = table.delete_item(
                Key={
                    pk_attribute: pk_value
                }
            )
        return response

    def scan(self, table_name, attribute=None, value=None):
        try:
            table = resource.Table(table_name)
            if (attribute is None or value is None):
                response = table.scan()
                return response['Items']
            elif (attribute and value):
                response = table.scan(
                    TableName=table_name,
                    FilterExpression=Attr(attribute).eq(value)
                )
                return response['Items']
            else:
                return None
        except ClientError as e:
            logging.error(e)
    
    def query(self, table_name, condition, value):
        table = resource.Table(table_name)
        response = table.query(KeyConditionExpression=Key(condition).eq(value))
        return response
    
    def delete_table(self, table_name):
        response = client.delete_table(
            TableName=table_name
        )
        return response
    
    def check_for_table(self, table_name):
        current_tables = client.list_tables()['TableNames']
        if table_name in current_tables:
            print("Table " + table_name + " already exists")
            return True
        else:
            print("Table " + table_name + " does not exist")
            return False
    
    def create_tables(self):
        table_name = 'users'
        if not self.check_for_table(table_name):
            try:
                key_schema = [
                    {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'
                    }
                ]
                attribute_definitions = [
                    {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                    }
                ]
                provisioned_throughput = {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                } 
                resource.create_table(
                    TableName=table_name, KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions, 
                    ProvisionedThroughput=provisioned_throughput
                )
                print("Table " + table_name + " created")
            except ClientError as e:
                print("Error occurred when creating table " + table_name)
                logging.error(e)
        else:
            print("Table " + table_name + " already exists")

        table_name = 'posts'
        if not self.check_for_table(table_name):
            try:
                key_schema=[
                    {
                    'AttributeName': 'post_id',
                    'KeyType': 'HASH'
                    }
                ]
                attribute_definitions=[
                    {
                    'AttributeName': 'post_id',
                    'AttributeType': 'S'
                    }
                ]
                provisioned_throughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
                resource.create_table(
                    TableName=table_name, KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions, 
                    ProvisionedThroughput=provisioned_throughput
                )
                print("Table " + table_name + " created")
            except ClientError as e:
                print("Error occurred when creating table " + table_name)
                logging.error(e)
        else:
            print("Table " + table_name + " already exists")

        table_name = 'comments'
        if not self.check_for_table(table_name):
            try:
                key_schema=[
                    {
                    'AttributeName': 'comment_id',
                    'KeyType': 'HASH'
                    }  
                ]
                attribute_definitions=[
                    {
                    'AttributeName': 'comment_id',
                    'AttributeType': 'S'
                    },
                ]
                provisioned_throughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
                resource.create_table(
                    TableName=table_name, KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions, 
                    ProvisionedThroughput=provisioned_throughput
                )
                print("Table " + table_name + " created")
            except ClientError as e:
                print("Error occurred when creating table " + table_name)
                logging.error(e)
        else:
            print("Table " + table_name + " already exists")

        table_name = 'likes'
        if not self.check_for_table(table_name):
            try:
                key_schema=[
                    {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'
                    },
                    {
                    'AttributeName': 'post_id',
                    'KeyType': 'RANGE'
                    }
                ]
                attribute_definitions=[
                    {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                    },
                    {
                    'AttributeName': 'post_id',
                    'AttributeType': 'S'
                    }
                ]
                provisioned_throughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
                resource.create_table(
                    TableName=table_name, KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions, 
                    ProvisionedThroughput=provisioned_throughput
                )
                print("Table " + table_name + " created")
            except ClientError as e:
                print("Error occurred when creating table " + table_name)
                logging.error(e)
        else:
            print("Table " + table_name + " already exists")

        table_name = 'friends'
        if not self.check_for_table(table_name):
            try:
                key_schema=[
                    {
                    'AttributeName': 'email_1',
                    'KeyType': 'HASH'
                    },
                    {
                    'AttributeName': 'email_2',
                    'KeyType': 'RANGE'
                    }
                ]
                attribute_definitions=[
                    {
                    'AttributeName': 'email_1',
                    'AttributeType': 'S'
                    },
                    {
                    'AttributeName': 'email_2',
                    'AttributeType': 'S'
                    }
                ]
                provisioned_throughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
                resource.create_table(
                    TableName=table_name, KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions, 
                    ProvisionedThroughput=provisioned_throughput
                )
                print("Table " + table_name + " created")
            except ClientError as e:
                print("Error occurred when creating table " + table_name)
                logging.error(e)
        else:
            print("Table " + table_name + " already exists")