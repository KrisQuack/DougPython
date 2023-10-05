import os

from azure.cosmos.aio import CosmosClient


class DatabaseConfig:
    def __init__(self):
        connection_string = os.environ.get('COSMOS_CONNECTION_STRING')
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.get_database_client('DougBot')
        self.BotSettings = self.database.get_container_client('BotSettings')
        self.Users = self.database.get_container_client('Users')
        self.Messages = self.database.get_container_client('Messages')
