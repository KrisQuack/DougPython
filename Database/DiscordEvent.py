import logging
import uuid

from discord import Member, Message, AuditLogEntry

from Database.DatabaseConfig import DatabaseConfig

class DiscordEvent:
    def __init__(self, database: DatabaseConfig):
        self.database = database
        self.dict = None

    def get_all_events(self):
        query = "SELECT * FROM DiscordEvents"
        items = self.database.DiscordEvents.query_items(query=query)
        return items

    def get_all_events_by_key(self, key: str, value):
        query = f"SELECT * FROM c WHERE c.{key} = '{value}'"
        items = self.database.DiscordEvents.query_items(query=query)
        return items

    async def get_event(self, id):
        try:
            # Try to get the event from the database
            self.dict = await self.database.DiscordEvents.read_item(str(id), str(id))
        except:
            # If the event doesn't exist, insert them into the database
            self.dict = None

    async def get_event_by_key(self, key: str, value):
        ### Somehow do this without the looping events
        query = f"SELECT * FROM DiscordEvents u WHERE u.{key} = '{value}'"
        items = self.database.Users.query_items(query=query)
        async for item in items:
            self.dict = item
        return self

    async def add_event(self, eventDict):
        try:
            # Perform the upsert operation
            await self.database.DiscordEvents.upsert_item(body=eventDict)
        except Exception as e:
            logging.getLogger("DiscordEvents").error(f"{e}")

    async def process_audit_log(self, audit_log_entry: AuditLogEntry):
        pass