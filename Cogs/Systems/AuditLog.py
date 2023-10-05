from asyncio import sleep
from datetime import datetime, timezone
import logging

import discord
from discord.ext import commands

from Database.User import User
from Database.Message import Message

class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await User(self.client.database).get_user(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await sleep(1)
        # Check if the member was kicked or banned
        reason = "Left"
        async for entry in member.guild.audit_logs(limit=1, user=member):
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
        await sleep(1)
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
            user_dict.setdefault('update_logs', []).append(update_log)

        await User(self.client.database).update_user(str(after.id),user_dict)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Add event to database
        await Message(self.client.database).get_message(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await sleep(1)
        if message.author.bot:
            return
        message_dict = await Message(self.client.database).get_message(message)
        # Check if the message was deleted by a mod
        async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete, user=message.author):
            if entry.target.id == message.author.id:
                message_dict['deleted_by'] = str(entry.user.id)
        message_dict['deleted_at'] = message.created_at.astimezone(timezone.utc).isoformat()
        await Message(self.client.database).update_message(str(message.id), message_dict)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await sleep(1)
        if before.author.bot:
            return
        message_dict = await Message(self.client.database).get_message(after)

        edit = {'edited_at': after.edited_at.astimezone(timezone.utc).isoformat(), 'content': after.content}
        message_dict['edits'].append(edit)
        message_dict['updated_at'] = after.edited_at.astimezone(timezone.utc).isoformat()

        await Message(self.client.database).update_message(str(after.id), message_dict)

async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
