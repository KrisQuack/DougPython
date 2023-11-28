import logging
import os
import sys
import traceback

import discord
from discord import Embed, Color
from discord.app_commands import AppCommandError
from discord.ext import commands

from Classes.Database.BotSettings import BotSettings, get_settings
from Classes.GPT import GPT
from Classes.Twitch import TwitchBot
from LoggerHandler import LoggerHandler


class Client(commands.Bot):
    def __init__(self):
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
                self.settings: BotSettings = await get_settings(self)
                self.openai = GPT(
                    api_version=self.settings.ai_api_version,
                    azure_endpoint=self.settings.ai_azure_endpoint,
                    api_key=self.settings.ai_api_key,
                )
                await self.register_cogs()
                self.tree.on_error = self.on_interaction_fail
                synced = await self.tree.sync()
                logging.getLogger("Main").info(f'Command tree synced: {len(synced)}')
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
            except Exception as e:
                logging.getLogger("Main").error(f'Failed to initialize: {e}')
                os._exit(1)
        logging.getLogger("Main").info(f'Guild available: {guild.name} ({guild.id})')

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
            await self.settings.log_channel.send(embed=embed)

    async def on_interaction_fail(self, interaction: discord.Interaction, error: AppCommandError):
        await interaction.response.send_message(error, ephemeral=True)
        embed = await self.send_interaction_embed(interaction, f"Command Failed: {interaction.data['name']}",
                                                  Color.red(), error)
        await self.settings.log_channel.send(embed=embed)
        formatted_traceback = traceback.format_exception(type(error), error, error.__traceback__)
        logging.getLogger("App_Command").error(
            f'Command {interaction.data["name"]} failed: {error}\n\n{formatted_traceback}')

    async def register_cogs(self):
        # Start the Twitch bot
        await TwitchBot(self).run()
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
        logging.getLogger("Cogs").info(f'Loaded ({len(loadedCogs)}): {", ".join(loadedCogs)}')
        logging.getLogger("Cogs").info(f'Failed ({len(failedCogs)}): {", ".join(failedCogs)}')


# Create the logger
logger = LoggerHandler(os.environ.get('LOGGER_WEBHOOK'))
discord.utils.setup_logging(level=logging.INFO, handler=logger)
# Log Python version as error to cause ping
logging.error(f'Python version: {sys.version}')
# Start the client
client = Client()
client.run(os.environ.get('TOKEN'), log_handler=None)
