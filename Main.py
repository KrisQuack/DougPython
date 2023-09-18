import asyncio
import os

import discord
from discord import Embed, Color
from discord.ext import commands

from Database.BotSettings import BotSettings


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all(),
                         help_command=None)
        # Define first run
        self.first_run = True

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_guild_available(self, guild: discord.Guild):
        if self.first_run:
            await self.register_cogs()
            synced = await self.tree.sync()
            print(f'Command tree synced: {len(synced)}')
            self.first_run = False
        print(f'Guild available: {guild.name} ({guild.id})')

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            embed = Embed(title=f"Command Used: {interaction.data['name']}", color=Color.green())
            embed.add_field(name="Used by", value=f"{interaction.user.name} ({interaction.user.id})", inline=False)
            embed.add_field(name="Used In", value=f"{interaction.channel.name} ({interaction.channel.id})",
                            inline=False)
            if interaction.data.get('options') is not None:
                options_str = "\n".join(
                    [f"{option['name']}: {option['value']}" for option in interaction.data['options']])
                embed.add_field(name="Command Options", value=options_str, inline=False)
            embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})",
                             icon_url=interaction.user.avatar.url)
            # Send to log channel
            await(await BotSettings.get_log_channel(self)).send(embed=embed)

        if interaction.command_failed:
            print(interaction.command_failed)

    async def register_cogs(self):
        # Automatically load cogs from the 'Cogs/Commands/' folder
        for filename in os.listdir('./Cogs/Commands'):
            if filename.endswith('.py'):
                print(f'Loading {filename[:-3]}')
                await self.load_extension(f'Cogs.Commands.{filename[:-3]}')
        # Automatically load cogs from the 'Cogs/Systems/' folder
        for filename in os.listdir('./Cogs/Systems'):
            if filename.endswith('.py'):
                print(f'Loading {filename[:-3]}')
                await self.load_extension(f'Cogs.Systems.{filename[:-3]}')
        print('All cogs loaded')


client = Client()
client.run(os.environ.get('TOKEN'))