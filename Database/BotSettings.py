import os

from sqlalchemy import Column, Integer, String, ARRAY, select
from Database.DatabaseConfig import Session, Base
from discord.ext import commands

class BotSettings(Base):
    __tablename__ = 'bot_settings'

    id = Column(Integer, primary_key=True)
    reaction_filter_emotes = Column(ARRAY(String))
    twitch_bot_name = Column(String)
    twitch_bot_refresh_token = Column(String)
    twitch_channel_name = Column(String)
    twitch_client_id = Column(String)
    twitch_client_secret = Column(String)
    guild_id = Column(Integer)
    dm_receipt_channel_id = Column(Integer)
    log_blacklist_channels = Column(ARRAY(Integer))
    log_channel_id = Column(Integer)
    reaction_filter_channels = Column(ARRAY(Integer))
    report_channel_id = Column(Integer)
    mod_role_id = Column(Integer)

    @classmethod
    async def get_reaction_filter_emotes(cls):
        async with Session() as session:
            stmt = select(cls.reaction_filter_emotes)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def set_reaction_filter_emotes(cls, value):
        async with Session() as session:
            stmt = cls.__table__.update().values(reaction_filter_emotes=value)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_twitch_bot_name(cls):
        async with Session() as session:
            stmt = select(cls.twitch_bot_name)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def get_twitch_bot_refresh_token(cls):
        async with Session() as session:
            stmt = select(cls.twitch_bot_refresh_token)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def get_twitch_channel_name(cls):
        async with Session() as session:
            stmt = select(cls.twitch_channel_name)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def get_twitch_client_id(cls):
        async with Session() as session:
            stmt = select(cls.twitch_client_id)
            result = await session.execute(stmt)
            return result.scalar()
        
    @classmethod
    async def get_twitch_client_secret(cls):
        async with Session() as session:
            stmt = select(cls.twitch_client_secret)
            result = await session.execute(stmt)
            return result.scalar()
        
    @classmethod
    async def get_guild(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.guild_id)
            result = await session.execute(stmt)
            return client.get_guild(result.scalar())
        
    @classmethod
    async def get_dm_receipt_channel(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.dm_receipt_channel_id)
            result = await session.execute(stmt)
            return client.get_channel(result.scalar())
        
    @classmethod
    async def get_log_blacklist_channels(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.log_blacklist_channels)
            result = await session.execute(stmt)
            return [client.get_channel(channel_id) for channel_id in result.scalar()]
        
    @classmethod
    async def get_log_channel(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.log_channel_id)
            result = await session.execute(stmt)
            return client.get_channel(result.scalar())
        
    @classmethod
    async def get_reaction_filter_channels(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.reaction_filter_channels)
            result = await session.execute(stmt)
            return [client.get_channel(channel_id) for channel_id in result.scalar()]
        
    @classmethod
    async def get_report_channel(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.report_channel_id)
            result = await session.execute(stmt)
            return client.get_channel(result.scalar())
        
    @classmethod
    async def get_mod_role(cls, client: commands.Bot):
        async with Session() as session:
            stmt = select(cls.guild_id, cls.mod_role_id)
            result = await session.execute(stmt)
            row = result.fetchone()
            if row:
                guild_id, mod_role_id = row
                guild = client.get_guild(guild_id)
                return guild.get_role(mod_role_id)
            return None