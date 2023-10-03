import logging
from datetime import datetime
from pytz import utc

from discord import Member, Message

from Database.DatabaseConfig import DatabaseConfig

class DiscordEvent:
    def __init__(self, database: DatabaseConfig):
        self.database = database
        self.dict = None

    def get_all_events(self):
        return self.database.Users.query_items(
            query='SELECT * FROM DiscordEvents',
            enable_cross_partition_query=True
        )

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

    def object_to_dict(self, obj):
        if isinstance(obj, Member):
            return {
                'id': str(obj.id),
                'name': obj.name,
                'global_name': obj.global_name,
                'nick': obj.nick,
                'roles': [role.id for role in obj.roles],
                'joined_at': obj.joined_at.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S.%f') if obj.joined_at else None,
                'created_at': obj.created_at.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S.%f') if obj.created_at else None,
                'avatar_url': str(obj.avatar.url) if obj.avatar else None,
            }
        elif isinstance(obj, Message):
            return {
                'id': str(obj.id),
                'author_id': str(obj.author.id),
                'channel_id': str(obj.channel.id),
                'reference': str(obj.reference.message_id) if obj.reference else None,
                'content': obj.content,
                'created_at': obj.created_at.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S.%f') if obj.created_at else None,
                'edited_at': obj.edited_at.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S.%f') if obj.edited_at else None,
                'attachments': [attachment.url for attachment in obj.attachments],
            }
        return None

    async def process_event(self, before=None, after=None):
        try:
            # Determine the type of event and set up the dict accordingly
            if isinstance(before, (Member, Message)) or isinstance(after, (Member, Message)):
                event_type = 'Member' if isinstance(before, Member) or isinstance(after, Member) else 'Message'
            else:
                raise Exception("Invalid object type.")

            # Fetch the existing entry from the database if it exists
            item_id = str(before.id if before else after.id)
            await self.get_event(item_id)

            # Create a dict for the before and after objects
            beforeDict = self.object_to_dict(before) if before else None
            afterDict = self.object_to_dict(after) if after else None

            # If there are both, prepare a changes dict showing the updated fields
            changesDict = {}
            if beforeDict and afterDict:
                changesDict = {key: afterDict[key] for key in afterDict if beforeDict.get(key) != afterDict.get(key)}

            # Prepare a new changes entry
            new_changes_entry = {
                datetime.utcnow().isoformat(): changesDict
            }

            # Handle the scenario where after is None, indicating a deletion or a member leaving
            if after is None:
                deletion_event = {
                    'deleted_at' if event_type == 'Message' else 'left_at': datetime.utcnow().isoformat(),
                }
                new_changes_entry[datetime.utcnow().isoformat()] = deletion_event

            # If it is a message, create or update the main entry dict
            if event_type == 'Message':
                message_id = before.id if before else after.id
                author_id = before.author.id if before else after.author.id
                if not self.dict:
                    # Create a new entry
                    self.dict = {
                        'id': str(message_id),
                        'messageID': message_id,
                        'authorID': author_id,
                        'eventType': event_type,
                        'datetime': datetime.utcnow().isoformat(),
                        'main_entry': beforeDict if before else afterDict,
                        'changes': {
                            'datetime': datetime.utcnow().isoformat(),
                            'changes': new_changes_entry
                        }
                    }
                else:
                    # Update the existing entry
                    self.dict['changes']['changes'].update(new_changes_entry)

            # If it is a member, create or update the main entry dict
            elif event_type == 'Member':
                member_id = before.id if before else after.id
                if not self.dict:
                    # Create a new entry
                    self.dict = {
                        'id': str(member_id),
                        'memberID': member_id,
                        'eventType': event_type,
                        'main_entry': beforeDict if before else afterDict,
                        'changes': {
                            'datetime': datetime.utcnow().isoformat(),
                            'changes': new_changes_entry
                        }
                    }
                else:
                    # Update the existing entry
                    self.dict['changes']['changes'].update(new_changes_entry)

            # Perform the upsert operation
            await self.database.DiscordEvents.upsert_item(body=self.dict)
        except Exception as e:
            logging.getLogger("DiscordEvents").error(f"Event: {event_type}\nID: {item_id}\n\n{e}")