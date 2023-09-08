import sys
import discord
from discord import app_commands
from discord.ext import commands


def is_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.client.is_owner(interaction.user)
    return app_commands.check(predicate)


class Shutdown(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="shutdown", description="Shuts down the bot")
    @app_commands.guild_only()
    @is_owner()
    async def Shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting down", ephemeral=True)
        sys.exit()


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Shutdown(self))
