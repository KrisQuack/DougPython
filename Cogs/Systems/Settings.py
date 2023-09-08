import os

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from discord.ext import commands
from discord.ext import commands, tasks


Base = declarative_base()


class BotSettings(Base):
    __tablename__ = 'bot_settings'

    id = Column(Integer, primary_key=True)
    token = Column(String)
    reaction_filter_emotes = Column(ARRAY(String))
    twitch_bot_name = Column(String)
    twitch_bot_refresh_token = Column(String)
    twitch_channel_name = Column(String)
    twitch_client_id = Column(String)
    twitch_client_secret = Column(String)
    twitch_eventsub_url = Column(String)
    guild_id = Column(Integer)
    dm_receipt_channel_id = Column(Integer)
    log_blacklist_channels = Column(ARRAY(Integer))
    log_channel_id = Column(Integer)
    reaction_filter_channels = Column(ARRAY(Integer))
    report_channel_id = Column(Integer)
    mod_role_id = Column(Integer)


class YouTubeSettings(Base):
    __tablename__ = 'youtube_settings'

    id = Column(Integer, primary_key=True)
    youtube_id = Column(String)
    mention_role_id = Column(Integer)
    post_channel_id = Column(Integer)
    guild_id = Column(Integer)


DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Settings:
    def __init__(self, client: commands.Bot = None):
        session = Session()

        # Fetch the bot settings
        bot_settings = session.query(BotSettings).first()
        if bot_settings:
            self.token = bot_settings.token
            self.reaction_filter_emotes = bot_settings.reaction_filter_emotes
            self.twitch_bot_name = bot_settings.twitch_bot_name
            self.twitch_bot_refresh_token = bot_settings.twitch_bot_refresh_token
            self.twitch_channel_name = bot_settings.twitch_channel_name
            self.twitch_client_id = bot_settings.twitch_client_id
            self.twitch_client_secret = bot_settings.twitch_client_secret
            self.twitch_eventsub_url = bot_settings.twitch_eventsub_url
            self.guild_id = bot_settings.guild_id
            self.dm_receipt_channel_id = bot_settings.dm_receipt_channel_id
            self.log_blacklist_channels = bot_settings.log_blacklist_channels
            self.log_channel_id = bot_settings.log_channel_id
            self.reaction_filter_channels = bot_settings.reaction_filter_channels
            self.report_channel_id = bot_settings.report_channel_id
            self.mod_role_id = bot_settings.mod_role_id

        # Fetch the guild
        if client:
            self.guild = client.get_guild(bot_settings.guild_id)
            self.dm_receipt_channel = client.get_channel(bot_settings.dm_receipt_channel_id)
            self.log_blacklist_channels = [client.get_channel(channel_id) for channel_id in
                                           bot_settings.log_blacklist_channels]
            self.log_channel = client.get_channel(bot_settings.log_channel_id)
            self.reaction_filter_channels = [client.get_channel(channel_id) for channel_id in
                                             bot_settings.reaction_filter_channels]
            self.report_channel = client.get_channel(bot_settings.report_channel_id)
            self.mod_role = self.guild.get_role(bot_settings.mod_role_id)

            # Fetch YouTube settings
            youtube_settings_list = session.query(YouTubeSettings).all()
            self.youtube_settings = []
            for yt in youtube_settings_list:
                yt_dict = {
                    "id": yt.youtube_id,
                    "mention_role": self.guild.get_role(yt.mention_role_id) if client else None,
                    "post_channel": client.get_channel(yt.post_channel_id) if client else None,
                    "guild_id": client.get_guild(yt.guild_id) if client else None
                }
                self.youtube_settings.append(yt_dict)

        session.close()


class SettingsRefresher(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.refresh_settings.start()

    @tasks.loop(minutes=1)  # Run this loop every minute
    async def refresh_settings(self):
        # Refresh the settings
        self.client.settings = Settings(self.client)

    @refresh_settings.before_loop
    async def before_refresh_settings(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(SettingsRefresher(client))
