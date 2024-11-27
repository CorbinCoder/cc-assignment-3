from botocore.exceptions import ClientError
from mysql.connector import Error
from tabulate import tabulate
import mysql.connector
import boto3
import config
import logging

global client
client = boto3.client('rds', region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id,
                            aws_secret_access_key=config.aws_secret_access_key)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
            db_name = "session_data"
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS{db_name}")
            connection.commit()
            logging.info(f"Database '{db_name}' created or already exists.")
            return True
        except ClientError as e:
            logging.error(e)
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Connection closed")

    def execute_query(self, query, values=None):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
            host=config.rds_hostname,
            port=3306,
            database=config.session_db_name,
            user=config.rds_secret_name,
            password=config.rds_secret_password,
            )
            if connection.is_connected():
                logging.info("Connected to MySQL database")
                cursor = connection.cursor(prepared=True)
                if values:
                    cursor.execute(query, values)
                    connection.commit()
                    logging.info(f"Query executed successfully. {cursor.rowcount} row(s) affected.")
                else:
                    results = cursor.execute(query)
                    cursor.execute(query)
                    print(results)
            else:
                print("Connection to MySQL database failed")
        except Error as e:
            logging.error(f"Error executing query: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logging.info("Connection closed.")

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