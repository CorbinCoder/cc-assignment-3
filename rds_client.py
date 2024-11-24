from botocore.exceptions import ClientError
from mysql.connector import Error
from tabulate import tabulate
import mysql.connector
import boto3
import config
import logging

global client, DB_NAME
client = boto3.client('rds')

class rds_client:

    def define_tables(self):
        TABLE = """ CREATE TABLE IF NOT EXISTS session_data (
          session_id TEXT PRIMARY KEY,
          start_datetime TEXT NOT NULL,
          end_datetime TEXT NOT NULL,
          ip_address TEXT NOT NULL
        ) """
        return TABLE

    def create_database(self):
        try:
            connection = mysql.connector.connect(
            host=config.rds_hostname,
            user=config.rds_secret_name,
            password=config.rds_secret_password,
        )
            cursor = connection.cursor()
            cursor.execute( """CREATE DATABASE IF NOT EXISTS {} """.format(config.rds_hostname))
        except ClientError as e:
            logging.error(e)
            if e.response['Error']['Code'] == 'DBAlreadyExists':
                var = True
            else:
                var = False
        return var

    def execute_query(self, query, values=None):
        connection = None
        try:
            connection = mysql.connector.connect(
            host=config.rds_hostname,
            database=config.session_db_name,
            user=config.rds_secret_name,
            password=config.rds_secret_password,
            )
            if connection.is_connected():
                print("Connected to MySQL database")
                if values:
                    cursor = connection.cursor(prepared=True)
                    cursor.execute(query, values)
                    connection.commit()
                else:
                    cursor = connection.cursor()
                    cursor.execute(query)
            else:
                print("Connection to MySQL database failed")
        except Error as e:
            logging.error(e)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Connection closed")

    def describe_instance(self):
        response = client.describe_db_instances(
            DBInstanceIdentifier=config.rds_identifier
        )
        return response

    def start_instance(self):
        response = client.start_db_instance(
            DBInstanceIdentifier=config.rds_identifier
        )
        print(response)

    def reboot_instance(self):
        response = client.reboot_db_instance(
            DBInstanceIdentifier=config.rds_identifier
        )
        print(response)
    
    def stop_instance(self):
        response = client.stop_db_instance(
            DBInstanceIdentifier=config.rds_identifier
        )
        print(response)

    def delete_instance(self):
        response = client.delete_db_instance(
            DBInstanceIdentifier=config.rds_identifier,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
        print(response)