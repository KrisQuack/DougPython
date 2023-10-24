import io
import sys
import aiohttp
import asyncio

import discord
from discord import app_commands, ui
from discord.ext import commands


class Ticket(commands.GroupCog, name="ticket"):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="open", description="Open a ticket for support")
    @app_commands.guild_only()
    async def open(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.client))

    @app_commands.command(name="close", description="Close a ticket")
    @app_commands.guild_only()
    async def close(self, interaction: discord.Interaction):
        async def fetch_attachment(session, url):
            async with session.get(url) as resp:
                return await resp.read()

        ticketCategory = self.client.get_channel(755181630305599488)
        closeChannel = self.client.get_channel(715024092914516011)
        ticketChannel = interaction.channel

        if ticketChannel.category_id == ticketCategory.id:
            ticketChat = [msg async for msg in ticketChannel.history(limit=sys.maxsize)]
            ticketChat.reverse()
            ticketString = "".join([f"{msg.author.display_name}: {msg.content}\n" for msg in ticketChat])

            all_attachments = []
            mentioned_users = {}
            async with aiohttp.ClientSession() as session:
                tasks = []
                for msg in ticketChat:
                    mentioned_users[msg.author.id] = msg.author.display_name
                    for attachment in msg.attachments:
                        tasks.append(fetch_attachment(session, attachment.url))

                all_attachments = await asyncio.gather(*tasks)

            mention_list = "\n".join(
                [f"{display_name} ({user_id})" for user_id, display_name in mentioned_users.items()])
            message = f"Closed ticket: {ticketChannel.name}\nParticipants:\n{mention_list}"
            # For each user in the ticket, send them a message with the ticket chat
            # Except for users with the mod role
            for user in ticketChannel.members:
                if user.guild_permissions.moderate_members or user.bot:
                    continue
                user_files = [discord.File(io.BytesIO(a), filename=f"attachment_{i}.png") for i, a in
                              enumerate(all_attachments)]
                user_files.append(discord.File(io.BytesIO(ticketString.encode('utf-8')), f'{ticketChannel.name}.txt'))
                await user.send(message, files=user_files)

            # Send the ticket chat to the close channel
            channel_files = [discord.File(io.BytesIO(a), filename=f"attachment_{i}.png") for i, a in
                             enumerate(all_attachments)]
            channel_files.append(discord.File(io.BytesIO(ticketString.encode('utf-8')), f'{ticketChannel.name}.txt'))
            await closeChannel.send(message, files=channel_files)

            await ticketChannel.delete()
        else:
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

    @app_commands.command(name="add_user", description="Add a user to a ticket")
    @app_commands.guild_only()
    async def add_user(self, interaction: discord.Interaction, user: discord.Member):
        # Get the ticket category
        ticketCategory = self.client.get_channel(755181630305599488)
        # Get the ticket channel
        ticketChannel = interaction.channel
        # Check if the ticket channel is in the ticket category
        if ticketChannel.category_id == ticketCategory.id:
            # Set the permissions for the ticket channel to include the user
            await ticketChannel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)
            # Send a success message
            await interaction.response.send_message(f"User added: {user.mention}", ephemeral=False)
        else:
            # Send an error message
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

    @app_commands.command(name="remove_user", description="Remove a user from a ticket")
    @app_commands.guild_only()
    async def remove_user(self, interaction: discord.Interaction, user: discord.Member):
        # Get the ticket category
        ticketCategory = self.client.get_channel(755181630305599488)
        # Get the ticket channel
        ticketChannel = interaction.channel
        # Check if the ticket channel is in the ticket category
        if ticketChannel.category_id == ticketCategory.id:
            # Set the permissions for the ticket channel to include the user
            await ticketChannel.set_permissions(user, read_messages=False, send_messages=False, view_channel=False)
            # Send a success message
            await interaction.response.send_message(f"User removed: {user.mention}", ephemeral=False)
        else:
            # Send an error message
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

class TicketModal(ui.Modal, title="Ticket"):
    def __init__(self, client: commands.Bot):
        super().__init__()
        self.client = client

    name = ui.TextInput(label="Name", placeholder="Enter a title for the ticket", max_length=32)
    description = ui.TextInput(label="Description", placeholder="Enter a description for the ticket", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        # Get the ticket category
        ticketCategory = self.client.get_channel(755181630305599488)
        # Create the ticket channel with the title as the name
        ticketChannel = await ticketCategory.create_text_channel(name=f'{self.name}')
        # Set the permissions for the ticket channel to include the user
        await ticketChannel.set_permissions(interaction.user, read_messages=True, send_messages=True, view_channel=True)
        # Send the ticket welcome message and description
        await ticketChannel.send(f'# Welcome to your ticket {interaction.user.mention}\n### Description\n{self.description}')
        # Send a success message
        await interaction.response.send_message(f"Ticket created: {ticketChannel.mention}", ephemeral=True)

async def setup(self: commands.Bot) -> None:
    await self.add_cog(Ticket(self))
