import logging
import sys
import time
from datetime import datetime, timezone, timedelta

import discord
from discord import RawMessageUpdateEvent, RawMessageDeleteEvent
from discord.ext import commands, tasks
from sqlalchemy.future import select

from Classes.Database.Message import Message, get_message, update_message, query_messages
from Classes.Database.User import User, get_user, update_user


class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.sync_database.start()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await get_user(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Check if the member was kicked or banned
        reason = "Left"
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == discord.AuditLogAction.kick:
                reason = f'Kicked: {entry.reason}'
            elif entry.action == discord.AuditLogAction.ban:
                reason = f'Banned: {entry.reason}'
        user: User = await get_user(member)

        update_log = {
            'left_at': datetime.utcnow().astimezone(timezone.utc).isoformat(),
            'reason': reason
        }
        user.edits.append(update_log)
        await update_user(user)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Get the user from the database
        user: User = await get_user(after)

        # Prepare update log dictionary
        update_log = {
            'edited_at': datetime.utcnow().astimezone(timezone.utc).isoformat(),
            'changes': {}
        }

        # Add changes to the log
        if before.name != after.name:
            update_log['changes']['name'] = {'before': before.name, 'after': after.name}
        if before.display_name != after.display_name:
            update_log['changes']['display_name'] = {'before': before.display_name, 'after': after.display_name}
        if before.nick != after.nick:
            update_log['changes']['nick'] = {'before': before.nick, 'after': after.nick}
        if before.roles != after.roles:
            before_roles = set(role.id for role in before.roles)
            after_roles = set(role.id for role in after.roles)
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            if added_roles or removed_roles:
                update_log['changes']['roles'] = {
                    'added': list(added_roles),
                    'removed': list(removed_roles)
                }

        # Update the user's edits only if there were changes
        if update_log['changes']:
            user.edits.append(update_log)

        await update_user(user)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Add event to database
        await get_message(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        # Get the message from the server
        message = payload.cached_message
        if message is None:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        if message.author.bot:
            return
        dbMessage = await get_message(message)

        if message.edited_at:
            edit = {'edited_at': message.edited_at.astimezone(timezone.utc).isoformat(), 'content': message.content}
            dbMessage.edits.append(edit)
            dbMessage.updated_at = message.edited_at.astimezone(timezone.utc).replace(tzinfo=None)

            await update_message(dbMessage)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        # Get the message from the database
        messageQuery = await query_messages(select(Message).where(Message.id == str(payload.message_id)))
        message: Message = messageQuery[0]
        if message:
            # Check if the message was deleted by a mod
            async for entry in self.client.settings.guild.audit_logs(limit=1,
                                                                     action=discord.AuditLogAction.message_delete):
                if str(entry.target.id) == message.user_id:
                    message.deleted_by = str(entry.user.id)
            message.deleted_at = datetime.utcnow().astimezone(timezone.utc).replace(tzinfo=None)
            await update_message(message)

    @tasks.loop(hours=3)
    async def sync_database(self):
        start_time = time.time()
        guild = self.client.settings.guild
        channels = guild.text_channels + list(guild.threads) + guild.voice_channels
        count = 0
        for channel in channels:
            # Get all messages in channel from the last 4 hours
            dateafter = datetime.utcnow() - timedelta(minutes=1)
            messages = [msg async for msg in channel.history(limit=sys.maxsize, after=dateafter)]
            if (len(messages) != 0):
                # Get all messages in database
                dbMessages = await query_messages(select(Message.id).where(
                    Message.channel_id == str(channel.id),
                    Message.created_at > dateafter.astimezone(timezone.utc).replace(tzinfo=None)
                ))
                # Loop through messages
                for message in messages:
                    # Check if message is in database
                    if not message.author.bot and all(str(message.id) != id for _ in dbMessages):
                        # If not, add it
                        await get_message(message)
                        count += 1
        # If any messages were added, log it
        if count == 0:
            logging.info(f'Database Synced {len(channels)} channels, took {round(time.time() - start_time, 0)} seconds')
        else:
            logging.error(
                f'Database Synced {len(channels)} channels, took {round(time.time() - start_time, 0)} seconds\n'
                f'Found {count} messages that were not in the database')

    @sync_database.before_loop
    async def before_sync_database(self):
        await self.client.wait_until_ready()


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
