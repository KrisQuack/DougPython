from datetime import timezone

import discord
from discord import Member
from azure.cosmos.aio import ContainerProxy

from Database.DatabaseConfig import DatabaseConfig


class Message:
    def __init__(self, database_config: DatabaseConfig):
        self.database = database_config
        self.container: ContainerProxy = self.database.Messages

    def get_all_messages(self):
        return self.container.query_items(
            query='SELECT * FROM m', continuation_token_limit=1
        )

    async def get_message(self, discMessage: discord.Message):
        try:
            # Try to get the message from the database
            message = await self.container.read_item(str(discMessage.id), str(discMessage.id))
            return message
        except:
            # If the user doesn't exist, insert them into the database
            message_dict = {
                'id': str(discMessage.id),
                'channel_id': str(discMessage.channel.id),
                'user_id': str(discMessage.author.id),
                'content': discMessage.content,
                'attachments': [attachment.url for attachment in discMessage.attachments],
                'created_at': discMessage.created_at.astimezone(timezone.utc).isoformat(),
                'edits': []
            }
            await self.container.upsert_item(body=message_dict)
            return message_dict

    async def update_message(self, message_id, update_dict):
        await self.container.replace_item(item=message_id, body=update_dict)

    async def query_messages(self, query):
        return self.container.query_items(query=query, continuation_token_limit=1)
