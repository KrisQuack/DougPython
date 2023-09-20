import os

import discord
from discord import app_commands
from discord.ext import commands

# from Database.DiscordMessage import DiscordMessage
# from Database.DiscordMember import DiscordMember


class Owner(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    def check_if_it_is_me(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 130062174918934528

    @app_commands.command(name="reboot", description="Reboot the bot")
    @app_commands.check(check_if_it_is_me)
    async def reboot(self, interaction: discord.Interaction):
        os.system('reboot')

    @app_commands.command(name="syncdatabase", description="Sync objects from the server to the database")
    @app_commands.check(check_if_it_is_me)
    async def reboot(self, interaction: discord.Interaction, message_count: int = 1000):
        await interaction.response.send_message("Syncing database...")
        # Get all current database values
        current_members = await DiscordMember.get_all()
        current_messages = await DiscordMessage.get_all()
        # For each member in the server
        for member in interaction.guild.members:
            # If the member is not in the database, add them
            if member.id not in [member.id for member in current_members]:
                await DiscordMember.insert(member)
        await interaction.channel.send("Synced members")
        # For each channel in the server
        for channel in interaction.guild.text_channels:
            messages = [msg async for msg in channel.history(limit=message_count)]
            for message in messages:
                if message.id not in [message.id for message in current_messages]:
                    await DiscordMessage.insert(message)
            await interaction.channel.send(f"Synced Messages in {channel.name})")



async def setup(self: commands.Bot) -> None:
    await self.add_cog(Owner(self))
