from asyncio import sleep
from datetime import datetime, timezone, timedelta
import time
import logging
import sys

import discord
from discord import RawMessageUpdateEvent, RawMessageDeleteEvent
from discord.ext import commands, tasks

from Database.User import User
from Database.Message import Message

class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.sync_database.start()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await User(self.client.database).get_user(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Check if the member was kicked or banned
        reason = "Left"
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == discord.AuditLogAction.kick:
                reason = f'Kicked: {entry.reason}'
            elif entry.action == discord.AuditLogAction.ban:
                reason = f'Banned: {entry.reason}'
        user_dict = await User(self.client.database).get_user(member)

        user_dict['left_at'] = member.joined_at.astimezone(timezone.utc).isoformat()
        user_dict['reason'] = reason

        await User(self.client.database).update_user(str(member.id),user_dict)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Get the user from the database
        user_dict = await User(self.client.database).get_user(after)
        # Update the users information
        update_log = {
            'timestamp': after.joined_at.astimezone(timezone.utc).isoformat(),
            'changes': {}
        }
        if before.name != after.name:
            update_log['changes']['name'] = {'before': before.name, 'after': after.name}
        if before.global_name != after.global_name:
            update_log['changes']['global_name'] = {'before': before.global_name, 'after': after.global_name}
        if before.nick != after.nick:
            update_log['changes']['nick'] = {'before': before.nick, 'after': after.nick}
        if before.roles != after.roles:
            before_roles = set(role.id for role in before.roles)
            after_roles = set(role.id for role in after.roles)
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            if added_roles or removed_roles:  # Check if there are any role changes
                update_log['changes']['roles'] = {
                    'added': list(added_roles),
                    'removed': list(removed_roles)
                }

        if update_log['changes']:  # Only append log if there were changes
            user_dict.setdefault('edits', []).append(update_log)

        await User(self.client.database).update_user(str(after.id),user_dict)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Add event to database
        await Message(self.client.database).get_message(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        # Get the message from the server
        message = payload.cached_message
        if message is None:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        if message.author.bot:
            return
        message_dict = await Message(self.client.database).get_message(message)

        if message.edited_at:
            edit = {'edited_at': message.edited_at.astimezone(timezone.utc).isoformat(), 'content': message.content}
            message_dict['edits'].append(edit)
            message_dict['updated_at'] = message.edited_at.astimezone(timezone.utc).isoformat()

            await Message(self.client.database).update_message(str(message.id), message_dict)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        # Get the message from the database
        message_dict = await Message(self.client.database).query_messages(f"SELECT * FROM m WHERE m.id = '{payload.message_id}'")
        message_dict = [item async for item in message_dict]
        if message_dict:
            message_dict = message_dict[0]
            # Check if the message was deleted by a mod
            async for entry in self.client.settings.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if str(entry.target.id) == message_dict['user_id']:
                    message_dict['deleted_by'] = str(entry.user.id)
            message_dict['deleted_at'] = datetime.utcnow().astimezone(timezone.utc).isoformat()
            await Message(self.client.database).update_message(str(payload.message_id), message_dict)

    @tasks.loop(hours=3)
    async def sync_database(self):
        start_time = time.time()
        guild = self.client.settings.guild
        channels = guild.text_channels + list(guild.threads) + guild.voice_channels
        count = 0
        for channel in channels:
            # Get all messages in channel from the last 4 hours
            dateafter = datetime.now() - timedelta(hours=4)
            messages = [msg async for msg in channel.history(limit=sys.maxsize, after=dateafter)]
            if (len(messages) != 0):
                # Get all messages in database
                dbMessages = await Message(self.client.database).query_messages(f"SELECT m.id FROM m WHERE m.channel_id = '{channel.id}' AND m.created_at > '{dateafter.astimezone(timezone.utc).isoformat()}'")
                dbMessageList = [item async for item in dbMessages]
                dbMessageList = [item['id'] for item in dbMessageList]
                # Loop through messages
                for message in messages:
                    # Check if message is in database
                    if not message.author.bot and str(message.id) not in dbMessageList:
                        # If not, add it
                        await Message(self.client.database).get_message(message)
                        count += 1
        # If any messages were added, log it
        if count == 0:
            logging.info(f'Database Synced {len(channels)} channels, took {round(time.time() - start_time, 0)} seconds')
        else:
            logging.error(f'Database Synced {len(channels)} channels, took {round(time.time() - start_time, 0)} seconds\n'
                          f'Found {count} messages that were not in the database')

    @sync_database.before_loop
    async def before_sync_database(self):
        await self.client.wait_until_ready()

async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
