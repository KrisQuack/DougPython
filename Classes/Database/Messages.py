from datetime import datetime
from datetime import timezone
from typing import Optional

from discord import Message


async def get_Message(message: Message, database):
    collection = database.Messages
    db_message = await collection.find_one({'_id': str(message.id)})
    if db_message is None and hasattr(message, 'content'):
        # Insert new member
        db_message = {
            '_id': str(message.id),
            'channel_id': str(message.channel.id),
            'user_id': str(message.author.id),
            'content': message.content,
            'attachments': [attachment.url for attachment in message.attachments],
            'created_at': message.created_at.astimezone(timezone.utc),
            'edits': []
        }
        await collection.insert_one(db_message)
    return db_message


async def update_message(db_message, database):
    collection = database.Messages
    await collection.update_one({'_id': db_message['_id']}, {'$set': db_message})


async def get_messages_by_channel(channel_id: str, database, start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None):
    collection = database.Messages
    query = {'channel_id': channel_id}

    if start_time and end_time:
        query['created_at'] = {'$gte': start_time, '$lte': end_time}
    elif start_time:
        query['created_at'] = {'$gte': start_time}
    elif end_time:
        query['created_at'] = {'$lte': end_time}
    cursor = collection.find(query)
    messages = await cursor.to_list(length=None)

    return messages


async def get_message_by_id(message_id: str, database):
    collection = database.Messages
    db_message = await collection.find_one({'_id': message_id})
    return db_message
