import asyncio
import logging
import sys
import time
from datetime import datetime, timezone, timedelta

import discord
from discord import Color, Embed, RawMessageUpdateEvent, RawMessageDeleteEvent
from discord.ext import commands, tasks

from Classes.Database.Members import get_member, update_member, get_all_members
from Classes.Database.Messages import get_Message, update_message, get_messages_by_channel

class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.sync_database.start()
        self.send_logs.start()
        self.log_buffer = []

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = Embed(title=f"User Joined", color=Color.green())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        accountAge = datetime.now(timezone.utc) - member.created_at.astimezone(timezone.utc)
        embed.add_field(name="Account Age", value=f"{accountAge.days} days", inline=False)
        self.log_buffer.append(embed)
        #OLD DB#
        await get_member(member, self.client.database)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = Embed(title=f"User Left", color=Color.red())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        self.log_buffer.append(embed)
        #OLD DB#
        # Check if the member was kicked or banned
        reason = "Left"
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == discord.AuditLogAction.kick:
                reason = f'Kicked: {entry.reason}'
            elif entry.action == discord.AuditLogAction.ban:
                reason = f'Banned: {entry.reason}'
        user_dict = await get_member(member, self.client.database)
        if user_dict:
            user_dict['left_at'] = member.joined_at.astimezone(timezone.utc)
            user_dict['reason'] = reason
            
            await update_member(user_dict, self.client.database)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        embed = Embed(title=f"Member Updated", color=Color.orange())
        if before.nick != after.nick:
            embed.add_field(name="Nickname", value=f"{before.nick} -> {after.nick}", inline=False)
        if before.name != after.name:
            embed.add_field(name="Name", value=f"{before.name} -> {after.name}", inline=False)
        if before.global_name != after.global_name:
            embed.add_field(name="Global Name", value=f"{before.global_name} -> {after.global_name}", inline=False)
        if before.roles != after.roles:
            # List what roles were added and removed
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            if added_roles:
                embed.add_field(name="Roles Added", value=", ".join([role.mention for role in added_roles]))
            if removed_roles:
                embed.add_field(name="Roles Removed", value=", ".join([role.mention for role in removed_roles]))
        embed.set_author(name=f"{after.name} ({after.id})", icon_url=after.display_avatar.url)
        if embed.fields:
            self.log_buffer.append(embed)
            
        # Get the user from the database
        user_dict = await get_member(after, self.client.database)
        # Update the users information
        update_log = {
            'timestamp': datetime.now().astimezone(timezone.utc),
            'changes': {}
        }
        if before.name != after.name:
            update_log['changes']['name'] = {'before': before.name, 'after': after.name}
        if before.global_name != after.global_name:
            update_log['changes']['global_name'] = {'before': before.global_name, 'after': after.global_name}
        if before.nick != after.nick:
            update_log['changes']['nick'] = {'before': before.nick, 'after': after.nick}
        if before.roles != after.roles:
            before_roles = set(str(role.id) for role in before.roles)
            after_roles = set(str(role.id) for role in after.roles)
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            if added_roles or removed_roles:  # Check if there are any role changes
                update_log['changes']['roles'] = {
                    'added': list(added_roles),
                    'removed': list(removed_roles)
                }

        if update_log['changes']:  # Only append log if there were changes
            user_dict.setdefault('edits', []).append(update_log)

        await update_member(user_dict, self.client.database)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        await get_Message(message, self.client.database)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            return

        # Create the main embed for the deleted message
        main_embed = Embed(title=f"Message Deleted in {message.channel.name}", color=Color.red())
        main_embed.url = message.jump_url
        # If message content is empty or none, set it to "Media/Embed"
        content = message.content if message.content else "Media/Embed"
        main_embed.add_field(name='Content', value=content[0:1000], inline=False)
        main_embed.set_author(name=f"{message.author.name} ({message.author.id})",
                              icon_url=message.author.display_avatar.url)

        # List to hold all the embeds
        all_embeds = [main_embed]

        # Add attachments as separate embeds to the list
        for attachment in message.attachments:
            attachment_embed = Embed(title=f"Attachment from {message.author.name}", color=Color.red())
            attachment_embed.set_image(url=attachment.url)
            all_embeds.append(attachment_embed)

        # Add all message embeds to the list
        for embed in message.embeds:
            all_embeds.append(embed)

        # Send all embeds in one go
        for embed in all_embeds:
            self.log_buffer.append(embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        if isinstance(after.channel, discord.DMChannel):
            return
        if before.content == after.content:
            return
        embed = Embed(title=f"Message Edited in {after.channel.name}", color=Color.orange())
        embed.url = after.jump_url
        embed.add_field(name="Before", value=before.content[0:1000], inline=False)
        embed.add_field(name="After", value=after.content[0:1000], inline=False)
        embed.set_author(name=f"{before.author.name} ({before.author.id})", icon_url=before.author.display_avatar.url)
        self.log_buffer.append(embed)
        
        
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        # Get the message from the server
        message = payload.cached_message
        if message is None:
            channel = self.client.get_channel(payload.channel_id)
            if channel is not None:
                message = await channel.fetch_message(payload.message_id)
        if message.author.bot:
            return
        message_dict = await get_Message(message, self.client.database)

        if message.edited_at:
            edit = {'edited_at': message.edited_at.astimezone(timezone.utc), 'content': message.content}
            message_dict.setdefault('edits', []).append(edit)
            message_dict['updated_at'] = message.edited_at.astimezone(timezone.utc)

            await update_message(message_dict, self.client.database)
            
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        # Get the message from the database
        temp_message = MockMessage(payload.message_id)
        message_dict = await get_Message(temp_message, self.client.database)
        if message_dict:
            # Check if the message was deleted by a mod
            async for entry in self.client.statics.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if str(entry.target.id) == message_dict['user_id']:
                    message_dict['deleted_by'] = str(entry.user.id)
            message_dict['deleted_at'] = datetime.utcnow().astimezone(timezone.utc)
            await update_message(message_dict, self.client.database)

    #########################
    # Log Sending Scheduler #
    #########################
            
    @tasks.loop(seconds=10)
    async def send_logs(self):
        while self.log_buffer:
            # Take the first 10 embeds from the buffer
            embeds_to_send = self.log_buffer[:10]
            # Remove these embeds from the buffer
            self.log_buffer = self.log_buffer[10:]
            # Send the embeds
            await self.client.statics.log_channel.send(embeds=embeds_to_send)


    #######################
    # Database Sync Tasks #
    #######################
    
    async def sync_messages(self, channels):
        message_count = 0
        for channel in channels:
            start_time = datetime.utcnow().astimezone(timezone.utc) - timedelta(hours=4)
            end_time = datetime.utcnow().astimezone(timezone.utc)
            messages = [msg async for msg in channel.history(limit=sys.maxsize, after=start_time)]
            if messages:
                dbMessages = await get_messages_by_channel(str(channel.id), self.client.database, start_time, end_time)
                dbMessages = [dbMessage['_id'] for dbMessage in dbMessages]
                for message in messages:
                    if not message.author.bot and str(message.id) not in dbMessages:
                        await get_Message(message, self.client.database)
                        message_count += 1
        return message_count

    async def sync_members(self, guild):
        members = [member async for member in guild.fetch_members(limit=sys.maxsize)]
        dbMembers = await get_all_members(self.client.database)
        dbMembers = [dbMember['_id'] for dbMember in dbMembers]

        async def process_member(member):
            if not member.bot and str(member.id) not in dbMembers:
                await get_member(member, self.client.database)
                return 1
            return 0

        member_counts = await asyncio.gather(*(process_member(member) for member in members))
        member_count = sum(member_counts)
        return member_count

    @tasks.loop(hours=3)
    async def sync_database(self):
        sync_start_time = time.time()
        guild: discord.Guild = self.client.statics.guild
        channels = guild.text_channels + list(guild.threads) + guild.voice_channels

        message_count = await self.sync_messages(channels)
        member_count = await self.sync_members(guild)

        if message_count == 0 and member_count == 0:
            logging.info(f'Database Synced {len(channels)} channels, took {round(time.time() - sync_start_time)-30} seconds')
        else:
            logging.error(f'Database Synced {len(channels)} channels, took {round(time.time() - sync_start_time)-30} seconds\n'
                        f'Found {message_count} messages that were not in the database\n'
                        f'Found {member_count} members that were not in the database')

    @sync_database.before_loop
    async def before_sync_database(self):
        await self.client.wait_until_ready()

    @send_logs.before_loop
    async def before_send_logs(self):
        await self.client.wait_until_ready()

async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))


class MockMessage:
    def __init__(self, id):
        self.id = id