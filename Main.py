import os

import discord
from discord.ext import commands

from Data.Settings import Settings


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all(), help_command=None)
        # Define first run
        self.first_run = True
        self.settings = Settings(None)

    async def on_ready(self):
        if self.first_run:
            self.settings = Settings(self)
            synced = await self.tree.sync()
            print(f'Command tree synced: {len(synced)}')
            print(f'Logged on as {self.user}!')
            self.first_run = False

    async def setup_hook(self):
        # Automatically load cogs from the 'Cogs/Commands/' folder
        for filename in os.listdir('./Cogs/Commands'):
            if filename.endswith('.py'):
                await self.load_extension(f'Cogs.Commands.{filename[:-3]}')
        # Automatically load cogs from the 'Cogs/Systems/' folder
        for filename in os.listdir('./Cogs/Systems'):
            if filename.endswith('.py'):
                await self.load_extension(f'Cogs.Systems.{filename[:-3]}')


tempSettings = Settings(None)
client = Client()
client.run(tempSettings.token)
