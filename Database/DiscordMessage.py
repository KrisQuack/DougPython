from datetime import datetime
from Database.DatabaseConfig import DatabaseConfig
from discord import Message

class DiscordMessage:
    def __init__(self, database: DatabaseConfig):
        self.container = database.DiscordMessage
        self.dict = None

    def get_all_messages(self):
        # Get all messages from the database
        query = "SELECT * FROM c"
        items = self.container.query_items(query=query)
        return items

    async def load_message(self, message_id):
        try:
            message_id_str = str(message_id)
            self.dict = await self.container.read_item(message_id_str,message_id_str)
        except Exception as e:
            self.dict = None
        
    async def update_message(self):
        await self.container.upsert_item(self.dict)
    
    async def insert_message(self, message: Message):
        # Check if message already exists
        await self.load_message(message.id)
        if self.dict is not None:
            return
        # Get the current time for the change
        current_time = datetime.utcnow().isoformat()
        # convert message to dict and insert
        await self.container.create_item(
          {
              "id": str(message.id),
              "author_id": str(message.author.id),
              "channel_id": str(message.channel.id),
              "jump_url": message.jump_url,
              "content": [{"value": message.content, "changed_at": current_time}],
              "created_at": message.created_at.isoformat(),
              "deleted_at": None
          }
        )

    async def update_message_content(self, message: Message, new_value: str):
      # Check if message already exists
      await self.load_message(message.id)
      if self.dict is None:
          await self.insert_message(message)
          return
      
      # Check if the new value is different from the last value in history
      if self.dict["content"][-1]['value'] != new_value:
          # Update the attribute's history
          current_time = datetime.utcnow().isoformat()
          self.dict["content"].append({"value": new_value, "changed_at": current_time})
          
          # Upsert the updated data back into the container
          await self.update_message()
    
    async def update_message_deleted(self, message: Message):
        # Check if message already exists
        await self.load_message(message.id)
        if self.dict is None:
            await self.insert_message(message)
            return
        
        self.dict["deleted_at"] = datetime.utcnow().isoformat()
        await self.update_message()