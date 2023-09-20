from sqlalchemy import Column, BigInteger, select
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from discord import Member
import datetime

from Database.DatabaseConfig import Session, Base

class DiscordMember(Base):
    __tablename__ = 'discord_members'

    id = Column(BigInteger, primary_key=True)
    user_name = Column(JSONB)  # Dictionary of timestamp and value
    display_name = Column(JSONB)  # Dictionary of timestamp and value
    nick = Column(JSONB)  # Dictionary of timestamp and value
    status = Column(JSONB)  # Dictionary of timestamp and value
    roles = Column(JSONB)  # Dictionary of timestamp and value
    joined_at = Column(JSONB)  # Dictionary of timestamp and value
    left_at = Column(JSONB)  # Dictionary of timestamp and value

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
    async def insert(cls, member: Member):
        async with Session() as session:
            result = await session.execute(select(cls).filter_by(id=member.id))
            existing_member = result.scalar_one_or_none()
            if existing_member:
                return
            now = datetime.datetime.now()
            new_member = cls(
                id=member.id,
                user_name={str(now): member.name},
                display_name={str(now): member.display_name},
                nick={str(now): member.nick} if member.nick else None,
                status={str(now): str(member.raw_status)},
                roles={str(now): [role.id for role in member.roles]},
                joined_at={str(now): str(member.joined_at)}
            )
            session.add(new_member)
            await session.commit()

    @classmethod
    async def get(cls, member_id: int):
        async with Session() as session:
            return session.query(cls).filter_by(id=member_id).first()