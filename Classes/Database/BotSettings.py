import logging
import os

from discord.ext import commands
from sqlalchemy import Column, String, ARRAY, Integer, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
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


# Define the settings model
class BotSettings(Base):
    __tablename__ = 'BotSettings'
    id = Column(Integer, primary_key=True)
    dm_receipt_channel_id = Column(String)
    guild_id = Column(String)
    log_blacklist_channels = Column(ARRAY(String))
    log_channel_id = Column(String)
    mod_role_id = Column(String)
    new_member_role_id = Column(String)
    full_member_role_id = Column(String)
    reaction_filter_channels = Column(ARRAY(String))
    reaction_filter_emotes = Column(ARRAY(String))
    report_channel_id = Column(String)
    twitch_bot_name = Column(String)
    twitch_bot_refresh_token = Column(String)
    twitch_channel_name = Column(String)
    twitch_client_id = Column(String)
    twitch_client_secret = Column(String)
    twitch_gambling_channel_id = Column(String)
    twitch_mod_channel_id = Column(String)
    youtube_settings = Column(JSONB)
    ai_api_version = Column(String)
    ai_azure_endpoint = Column(String)
    ai_api_key = Column(String)


async def get_settings(client: commands.Bot = None):
    async with async_session() as session:
        result = await session.execute(select(BotSettings))
        settings: BotSettings = result.scalars().first()
        if settings:
            # Set some discord attributes
            if client is not None:
                # Set attributes
                settings.dm_receipt_channel = client.get_channel(int(settings.dm_receipt_channel_id))
                settings.guild = client.get_guild(int(settings.guild_id))
                settings.log_blacklist_channels = [client.get_channel(int(channel_id)) for channel_id in
                                                   settings.log_blacklist_channels]
                settings.log_channel = client.get_channel(int(settings.log_channel_id))
                settings.reaction_filter_channels = [client.get_channel(int(channel_id)) for channel_id in
                                                     settings.reaction_filter_channels]
                settings.report_channel = client.get_channel(int(settings.report_channel_id))
                settings.twitch_gambling_channel = client.get_channel(int(settings.twitch_gambling_channel_id))
                settings.twitch_mod_channel = client.get_channel(int(settings.twitch_mod_channel_id))
                # Print if any are None
                if settings.dm_receipt_channel is None or settings.guild is None or settings.log_channel is None or settings.report_channel is None or len(
                        settings.log_blacklist_channels) != len(settings.log_blacklist_channels) or len(
                    settings.reaction_filter_channels) != len(settings.reaction_filter_channels):
                    logging.getLogger("BotSettings").error("BotSettings failed to load some discord attributes")
            return settings


async def update_youtube_settings(new_youtube_settings):
    async with async_session() as session:
        # Assuming there's only one settings row, you can directly update without a specific WHERE clause
        # If there can be multiple, you'd need to identify which row to update (e.g., by ID)
        await session.execute(
            update(BotSettings).
            where(BotSettings.id == 1).  # or whatever logic you need to identify the correct row
            values(youtube_settings=new_youtube_settings)
        )
        await session.commit()
