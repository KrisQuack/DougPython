import os
import sys

import discord
from discord import app_commands
from discord.ext import commands

from Database.DiscordMember import DiscordMember
from Database.DiscordMessage import DiscordMessage


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
    async def syncDatabase(self, interaction: discord.Interaction):
        await interaction.response.send_message("Syncing database...")

        # Get all members from the server and database
        discordMember = DiscordMember(self.client.database)
        guildUsers = [usr async for usr in interaction.guild.fetch_members(limit=sys.maxsize)]
        databaseUsers = discordMember.get_all_members()
        databaseUsersList = [item async for item in databaseUsers]

        # Remove guildUsers who are in databaseUsersList
        oldGuildUsersLen = len(guildUsers)
        guildUsers = [user for user in guildUsers if str(user.id) not in [usr["id"] for usr in databaseUsersList]]
        await interaction.channel.send(f"Skipped {oldGuildUsersLen - len(guildUsers)} members for eixsting in the database")

        processed_count = 0
        # For each member in the server
        status = await interaction.channel.send(f"Syncing {len(guildUsers)} members")
        for user in guildUsers:
            # Check if the member is already in the database
            if user.id in [usr["id"] for usr in databaseUsersList]:
                continue
            # Insert the member into the database
            await discordMember.insert_member(user)
            processed_count += 1
            # Send a status message every 100 members
            if processed_count % 100 == 0:
                await status.edit(content=f"Syncing {len(guildUsers)} members ({processed_count}/{len(guildUsers)})")
        
        # Get all messages from the server and database
        discordMessage = DiscordMessage(self.client.database)
        databaseMessages = discordMessage.get_all_messages()
        databaseMessagesList = [item async for item in databaseMessages]
        guildMessages = None
        # For each channel in the server
        channels = [channel for channel in interaction.guild.fetch_channels()]
        for channel in channels:
            # Get all messages from the channel and add to guildMessages
            guildMessages = [msg async for msg in channel.history(limit=sys.maxsize)]

        # Remove guildMessages who are in databaseMessagesList
        oldGuildMessagesLen = len(guildMessages)
        guildMessages = [msg for msg in guildMessages if str(msg.id) not in [msg["id"] for msg in databaseMessagesList]]
        await interaction.channel.send(f"Skipped {oldGuildMessagesLen - len(guildMessages)} messages for eixsting in the database")

        # For each message in the server
        processed_count = 0
        status = await interaction.channel.send(f"Syncing {len(guildMessages)} messages")
        for message in guildMessages:
            # Check if the message is already in the database
            if message.id in [msg["id"] for msg in databaseMessagesList]:
                continue
            # Insert the message into the database
            await discordMessage.insert_message(message)
            processed_count += 1
            # Send a status message every 100 messages
            if processed_count % 100 == 0:
                await status.edit(content=f"Syncing {len(guildMessages)} messages ({processed_count}/{len(guildMessages)})")
        
        # Send a final status message
        await interaction.channel.send(f"Synced {len(guildUsers)} members and {len(guildMessages)} messages")





async def setup(self: commands.Bot) -> None:
    await self.add_cog(Owner(self))
