import os

import discord
from discord import app_commands
from discord.ext import commands


class Owner(commands.GroupCog, name="owner"):
    def __init__(self, client: commands.Bot):
        self.client = client

    def check_if_it_is_me(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 130062174918934528

    @app_commands.command(name="reboot", description="Reboot the bot")
    @app_commands.check(check_if_it_is_me)
    async def reboot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Rebooting...")
        os._exit(1)

    @app_commands.command(name="reboot_twitch", description="Reboot the twitch bot")
    @app_commands.check(check_if_it_is_me)
    async def reboot_twitch(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.client.reload_extension("Cogs.Systems.TwitchBot")
        await interaction.followup.send("Twitch bot rebooted")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Owner(self))
