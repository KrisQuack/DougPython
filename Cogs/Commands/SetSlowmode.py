import discord
from discord import app_commands
from discord.ext import commands


class SetSlowmode(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="set_slowmode", description="Set the slow mode for a channel")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        channel="The channel to set the slow mode in",
        seconds="The amount of seconds to set the slow mode to"
    )
    async def set_slowmode(self, interaction: discord.Interaction, channel: discord.TextChannel = None,
                           seconds: int = 5):
        if seconds > 21600:
            await interaction.response.send_message('The maximum slow mode time is 21600 seconds.', ephemeral=True)
            return

        if channel is None:
            channel = interaction.channel

        await channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f'Set slow mode to {seconds} seconds in {channel.mention}',
                                                ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(SetSlowmode(self))
