from discord import Member

from Database.DatabaseConfig import DatabaseConfig


class User:
    def __init__(self, database: DatabaseConfig):
        self.database = database
        self.dict = None

    def get_all_users(self):
        return self.database.Users.query_items(
            query='SELECT * FROM Users',
            enable_cross_partition_query=True
        )

    async def get_user(self, member: Member):
        try:
            # Try to get the user from the database
            self.dict = await self.database.Users.read_item(str(member.id), str(member.id))
        except:
            # If the user doesn't exist, insert them into the database
            self.dict = await self.database.Users.upsert_item(body={'id': str(member.id)})

    async def get_user_by_key(self, key: str, value):
        ### Somehow do this without the looping users
        query = f"SELECT * FROM Users u WHERE u.{key} = '{value}'"
        items = self.database.Users.query_items(query=query)
        async for item in items:
            self.dict = item
        return self

    async def upsert_user(self, member: Member, key: str = None, value=None):
        if self.dict is None and member is not None:
            await self.get_user(member)
        elif self.dict is None and member is None:
            raise Exception("No member or dict provided")
        # Update the key-value pair if both are provided
        if key and value:
            self.dict[key] = value
        # Remove the key if it exists and value is None
        elif key and value is None:
            self.dict.pop(key, None)
        # Perform the upsert operation
        await self.database.Users.upsert_item(body=self.dict)
