from azure.cosmos import CosmosClient
import os

class DatabaseConfig:
    def __init__(self):
        connection_string = os.environ.get('COSMOS_CONNECTION_STRING')
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.create_database_if_not_exists('DougBot')