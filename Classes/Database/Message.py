import os
from datetime import datetime, timezone

import discord
from sqlalchemy import Column, String, JSON, DateTime, update
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get('DATABASE_URL')
# Asynchronous database engine
engine = create_async_engine(DATABASE_URL, echo=True)
# Session maker bound to the engine
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
# Base class for declarative models
Base = declarative_base()


# Define the Message model
class Message(Base):
    __tablename__ = 'messages'
    id = Column(String, primary_key=True)
    channel_id = Column(String)
    user_id = Column(String)
    content = Column(String)
    attachments = Column(ARRAY(String))
    created_at = Column(DateTime)
    edits = Column(JSON)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    deleted_by = Column(String)


async def get_message(discMessage: discord.Message):
    try:
        async with async_session() as session:
            result = await session.execute(select(Message).where(Message.id == str(discMessage.id)))
            message = result.scalars().first()
            if message:
                return message
            else:
                # If the message doesn't exist, insert it into the database
                message = Message(
                    id=str(discMessage.id),
                    channel_id=str(discMessage.channel.id),
                    user_id=str(discMessage.author.id),
                    content=discMessage.content,
                    attachments=[attachment.url for attachment in discMessage.attachments],
                    created_at=discMessage.created_at.astimezone(timezone.utc).replace(tzinfo=None),
                    edits=[]
                )
                session.add(message)
                await session.commit()
                return message
    except Exception as e:
        # Proper error handling goes here
        print(f"An error occurred: {e}")


async def update_message(message):
    async with async_session() as session:
        # Update the message
        await session.execute(
            update(Message).
            where(Message.id == message.id).
            values(
                content=message.content,
                attachments=[attachment.url for attachment in message.attachments],
                edits=message.edits,
                updated_at=datetime.utcnow().astimezone(timezone.utc).replace(tzinfo=None),
                deleted_at=message.deleted_at,
            )
        )
        await session.commit()


async def query_messages(orm_query):
    async with async_session() as session:
        result = await session.execute(orm_query)
        messages = result.scalars().all()
        return messages
