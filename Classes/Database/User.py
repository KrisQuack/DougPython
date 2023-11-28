import os
from datetime import timezone

import discord
from sqlalchemy import Column, String, DateTime, update
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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


# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    name = Column(String)
    global_name = Column(String)
    nick = Column(String)  # Allows NULL
    roles = Column(ARRAY(String))  # Storing role IDs as strings
    joined_at = Column(DateTime)
    created_at = Column(DateTime)
    edits = Column(ARRAY(JSONB))  # Array of JSONB to store edits history
    left_at = Column(DateTime)  # Allows NULL
    reason = Column(String)  # Allows NULL


async def get_user(discMember: discord.Member):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == str(discMember.id)))
        user = result.scalars().first()
        if user:
            return user
        else:
            # If the user doesn't exist, insert them into the database
            user = User(
                id=str(discMember.id),
                name=discMember.name,
                global_name=discMember.display_name,  # Assuming global_name is the display name
                nick=discMember.nick,
                roles=[str(role.id) for role in discMember.roles],
                joined_at=discMember.joined_at.astimezone(timezone.utc).replace(tzinfo=None),
                created_at=discMember.created_at.astimezone(timezone.utc).replace(tzinfo=None),
                edits=[]  # Assuming you will handle edits separately
            )
            session.add(user)
            await session.commit()
            return user


async def update_user(user):
    async with async_session() as session:
        # Update the user
        await session.execute(
            update(User).
            where(User.id == user.id).
            values(
                name=user.name,
                global_name=user.global_name,
                nick=user.nick,
                roles=user.roles,
                joined_at=user.joined_at,
                created_at=user.created_at,
                edits=user.edits,
                left_at=user.left_at,
                reason=user.reason
            )
        )
        await session.commit()


async def query_users(orm_query):
    async with async_session() as session:
        result = await session.execute(orm_query)
        users = result.scalars().all()
        return users
