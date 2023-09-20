from sqlalchemy import Column, String, BigInteger, select,ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from discord import Message

from Database.DatabaseConfig import Session, Base

class DiscordMessage(Base):
    __tablename__ = 'discord_messages'

    id = Column(BigInteger, primary_key=True)
    content = Column(JSONB)  # Dictionary of timestamp and value
    attachments = Column(ARRAY(String))
    created_at = Column(TIMESTAMP)
    jump_url = Column(String)
    reference = Column(BigInteger)
    author_id = Column(BigInteger, ForeignKey('discord_members.id'))
    channel_id = Column(BigInteger)
    deleted = Column(Boolean)

    @classmethod
    async def get_all(cls):
        async with Session() as session:
            stmt = select(cls)
            results = await session.execute(stmt)
            return results.scalars().all()

    async def update(self):
        async with Session() as session:
            session.add(self)
            await session.commit()

    @classmethod
    async def insert(cls, message: Message):
        async with Session() as session:
            result = await session.execute(select(cls).filter_by(id=message.id))
            existing_message = result.scalar_one_or_none()
            if existing_message:
                return
            new_message = cls(
                id=message.id,
                content={str(message.created_at): message.content},
                attachments=[attachment.url for attachment in message.attachments],
                created_at=message.created_at,
                jump_url=message.jump_url,
                reference=message.reference.message_id if message.reference else None,
                author_id=message.author.id,
                channel_id=message.channel.id,
                deleted=False  # Initially set to False
            )
            session.add(new_message)
            await session.commit()

    @classmethod
    async def get(cls, message_id: int):
        async with Session() as session:
            return session.query(cls).filter_by(id=message_id).first()