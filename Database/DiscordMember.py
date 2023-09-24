import logging
from datetime import datetime
from Database.DatabaseConfig import DatabaseConfig
from discord import Member

class DiscordMember:
    def __init__(self, database: DatabaseConfig):
        self.container = database.DiscordMember
        self.dict = None

    def get_all_members(self):
        # Get all members from the database
        query = "SELECT * FROM c"
        items = self.container.query_items(query=query)
        return items

    async def load_member(self, member_id):
        try:
            member_id_str = str(member_id)
            self.dict = await self.container.read_item(member_id_str,member_id_str)
        except Exception as e:
            self.dict = None
        
    async def update_member(self):
        await self.container.upsert_item(self.dict)
    
    async def insert_member(self, member: Member):
        # Check if member already exists
        await self.load_member(member.id)
        if self.dict is not None:
            return
        # Get the current time for the change
        current_time = datetime.utcnow().isoformat()
        # convert member to dict and insert
        await self.container.create_item(
          {
              "id": str(member.id),
              "name": [{"value": member.name, "changed_at": current_time}],
              "global_name": [{"value": member.global_name, "changed_at": current_time}],
              "nick": [{"value": member.nick, "changed_at": current_time}],
              "created_at": member.created_at.isoformat(),
              "joined_at": member.joined_at.isoformat(),
          }
        )

    async def update_name_attribute(self, member: Member, attribute: str, new_value: str):
      # Ensure the attribute is one of the ones we want to track
      if attribute not in ["name", "display_name", "global_name", "nick"]:
          logging.error(f"Invalid attribute: {attribute}")
          return

      # Check if member already exists
      await self.load_member(member.id)
      if self.dict is None:
          await self.insert_member(member)
          return
      
      # Check if the new value is different from the last value in history
      if self.dict[attribute][-1]['value'] != new_value:
          # Update the attribute's history
          current_time = datetime.utcnow().isoformat()
          self.dict[attribute].append({"value": new_value, "changed_at": current_time})
          
          # Upsert the updated data back into the container
          await self.update_member()