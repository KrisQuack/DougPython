import asyncio

import discord
from discord import app_commands
from discord.ext import commands


class Typing(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="typing", description="Make the bot type in a channel for a given time")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        channel="The channel to type in",
        seconds="The amount of seconds to type for"
    )
    async def typing(self, interaction: discord.Interaction, channel: discord.TextChannel, seconds: int):
        await interaction.response.defer(ephemeral=True)
        if (seconds > 300):
            await interaction.followup.send('You cannot make me type for more than 5 minutes!')
            return
        await interaction.followup.send('Typing')
        async with channel.typing():
            await asyncio.sleep(seconds)
        await interaction.followup.send('Done typing')


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Typing(self))
