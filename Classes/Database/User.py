from datetime import timezone

from discord import Member
from azure.cosmos.aio import ContainerProxy

from Classes.Database.DatabaseConfig import DatabaseConfig


class User:
    def __init__(self, database_config: DatabaseConfig):
        self.database = database_config
        self.container: ContainerProxy = self.database.Users

    async def get_user(self, discMember: Member):
        try:
            # Try to get the user from the database
            user = await self.container.read_item(str(discMember.id), str(discMember.id))
            return user
        except:
            # If the user doesn't exist, insert them into the database
            user_dict = {
                'id': str(discMember.id),
                'name': discMember.name,
                'global_name': discMember.global_name,
                'nick': discMember.nick,
                'roles': [role.id for role in discMember.roles],
                'joined_at': discMember.joined_at.astimezone(timezone.utc).isoformat(),
                'created_at': discMember.created_at.astimezone(timezone.utc).isoformat(),
            }
            await self.container.upsert_item(body=user_dict)
            return user_dict

    async def update_user(self, user_id, update_dict):
        await self.container.replace_item(item=user_id, body=update_dict)

    async def query_users(self, query):
        return self.container.query_items(query=query, continuation_token_limit=1)
