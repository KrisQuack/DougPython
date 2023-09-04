import os
import discord
from discord import Embed, Color
from discord.ext import commands
from Data.Settings import Settings
from Cogs.Systems.Verification import VerifyButton


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all(), help_command=None)
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
            await self.settings.log_channel.send(embed=embed)

        if interaction.command_failed:
            print(interaction.command_failed)

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
