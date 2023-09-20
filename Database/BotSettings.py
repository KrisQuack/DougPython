import logging
from Database.DatabaseConfig import DatabaseConfig
from discord.ext import commands

class YouTubeSetting:
    def __init__(self, data):
        self.id = data['id']
        self.youtube_id = data['youtube_id']
        self.mention_role_id = data['mention_role_id']
        self.post_channel_id = data['post_channel_id']
        self.last_video_id = data['last_video_id']


class BotSettings:
    def __init__(self, client: commands.Bot = None):
        database = DatabaseConfig().database
        self.container = database.get_container_client('BotSettings')
        self.get_settings(client)
        logging.info("Loaded BotSettings")

    def get_settings(self, client: commands.Bot):
      # Load settings from database
      result = self.container.read_item('1', '1')
      self.settingDict = result
      # Set settings as attributes
      self.youtube_settings = [YouTubeSetting(data) for data in result['youtube_settings']]
      # Set some discord attributes
      if client is not None:
        # Get int values
        dm_receipt_channel_id = int(result['dm_receipt_channel_id'])
        guild_id = int(result['guild_id'])
        log_blacklist_channels = [int(channel_id) for channel_id in result['log_blacklist_channels']]
        log_channel_id = int(result['log_channel_id'])
        mod_role_id = int(result['mod_role_id'])
        reaction_filter_channels = [int(channel_id) for channel_id in result['reaction_filter_channels']]
        report_channel_id = int(result['report_channel_id'])
        # Set attributes
        self.dm_receipt_channel = client.get_channel(dm_receipt_channel_id)
        self.guild = client.get_guild(guild_id)
        self.log_blacklist_channels = [client.get_channel(channel_id) for channel_id in log_blacklist_channels]
        self.log_channel = client.get_channel(log_channel_id)
        self.mod_role = self.guild.get_role(mod_role_id)
        self.reaction_filter_channels = [client.get_channel(channel_id) for channel_id in reaction_filter_channels]
        self.report_channel = client.get_channel(report_channel_id)
        # Print if any are None
        if self.dm_receipt_channel is None or self.guild is None or self.log_channel is None or self.mod_role is None or self.report_channel is None or len(self.log_blacklist_channels) != len(log_blacklist_channels) or len(self.reaction_filter_channels) != len(reaction_filter_channels):
          logging.error("BotSettings failed to load some discord attributes")
    
    def update_settings(self):
        self.container.upsert_item(self.settingDict)
        logging.info(f"Updated BotSettings")