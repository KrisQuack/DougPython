import logging
import os
import sys
import traceback

import discord
from discord import Embed, Color
from discord.app_commands import AppCommandError
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from Classes.GPT import GPT
from Classes.WebhookLogging import WebhookLogging


class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.presences = False
        intents.guild_typing = False
        intents.dm_typing = False
        intents.voice_states = False

        super().__init__(command_prefix='✵', intents=discord.Intents.all(),
                         help_command=None)
        # Define first run
        self.first_run = True

    async def on_ready(self):
        logging.getLogger("Main").info(f'Logged on as {self.user}!')

    async def on_guild_available(self, guild: discord.Guild):
        if self.first_run:
            try:
                self.first_run = False
                self.mongo = AsyncIOMotorClient(os.environ.get('MONGO_URI'))
                self.database = self.mongo.DougBot
                await self.load_settings()
                # Create the logger
                logger = WebhookLogging(self)
                await logger.run_polling()
                discord.utils.setup_logging(level=logging.INFO, handler=logger)
                # Log Python version as error to cause ping
                logging.warning(f'Python version: {sys.version}')
                self.openai = GPT(
                    api_version=self.settings['ai_api_version'],
                    azure_endpoint=self.settings['ai_azure_endpoint'],
                    api_key=self.settings['ai_api_key'],
                )
                await self.register_cogs()
                self.tree.on_error = self.on_interaction_fail
                synced = await self.tree.sync()
                logging.getLogger("Main").info(f'Command tree synced: {len(synced)}')
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
            except Exception as e:
                logging.getLogger("Main").error(f'Failed to initialize: {e}\n{traceback.format_exc()}')
                os._exit(1)
        logging.getLogger("Main").info(f'Guild available: {guild.name} ({guild.id})')

    async def load_settings(self):
        self.settings = await self.database.BotSettings.find_one()
        self.statics = type('', (), {})()
        self.statics.dm_receipt_channel = client.get_channel(int(self.settings['dm_receipt_channel_id']))
        self.statics.guild = client.get_guild(int(self.settings['guild_id']))
        self.statics.log_blacklist_channels = [client.get_channel(int(channel_id)) for channel_id in
                                               self.settings['log_blacklist_channels']]
        self.statics.log_channel = client.get_channel(int(self.settings['log_channel_id']))
        self.statics.reaction_filter_channels = [client.get_channel(int(channel_id)) for channel_id in
                                                 self.settings['reaction_filter_channels']]
        self.statics.report_channel = client.get_channel(int(self.settings['report_channel_id']))
        self.statics.twitch_gambling_channel = client.get_channel(int(self.settings['twitch_gambling_channel_id']))
        self.statics.twitch_mod_channel = client.get_channel(int(self.settings['twitch_mod_channel_id']))
        self.statics.mod_channel = client.get_channel(int(self.settings['mod_channel_id']))

    async def send_interaction_embed(self, interaction: discord.Interaction, title: str, color: Color,
                                     error: AppCommandError = None):
        embed = Embed(title=title, color=color)
        embed.add_field(name="Used by", value=f"{interaction.user.name} ({interaction.user.id})", inline=False)
        embed.add_field(name="Used In", value=f"{interaction.channel.name} ({interaction.channel.id})", inline=False)

        if interaction.data.get('options') is not None:
            options_str = "\n".join(
                [f"{option['name']}: {option.get('value', 'N/A')}" for option in interaction.data['options']])
            embed.add_field(name="Command Options", value=options_str, inline=False)

        if error:
            embed.add_field(name="Error", value=error, inline=False)

        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})",
                         icon_url=interaction.user.display_avatar.url)
        return embed

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command and not interaction.command_failed:
            embed = await self.send_interaction_embed(interaction, f"Command Used: {interaction.data['name']}",
                                                      Color.green())
            await self.statics.log_channel.send(embed=embed)

    async def on_interaction_fail(self, interaction: discord.Interaction, error: AppCommandError):
        await interaction.response.send_message(error, ephemeral=True)
        embed = await self.send_interaction_embed(interaction, f"Command Failed: {interaction.data['name']}",
                                                  Color.red(), error)
        await self.statics.log_channel.send(embed=embed)
        formatted_traceback = traceback.format_exception(type(error), error, error.__traceback__)
        logging.getLogger("App_Command").error(
            f'Command {interaction.data["name"]} failed: {error}\n\n{formatted_traceback}')

    async def register_cogs(self):
        # Automatically load cogs from the 'Cogs/' folder and its subfolders
        loadedCogs = []
        failedCogs = []
        for dirpath, dirnames, filenames in os.walk('./Cogs'):
            for filename in filenames:
                if filename.endswith('.py'):
                    # Construct the extension name by converting file path to Python's dot notation
                    try:
                        extension = dirpath.replace('./', '').replace('/', '.') + '.' + filename[:-3]
                        await self.load_extension(extension)
                        loadedCogs.append(extension)
                    except Exception as e:
                        failedCogs.append(extension)
                        logging.getLogger("Cogs").error(f'Failed to load extension {extension}: {e}')
        logging.getLogger("Cogs").info(f'Loaded ({len(loadedCogs)}): {", ".join(loadedCogs)}')
        logging.getLogger("Cogs").info(f'Failed ({len(failedCogs)}): {", ".join(failedCogs)}')


# Start the client
client = Client()
client.run(os.environ.get('TOKEN'), log_handler=None)
