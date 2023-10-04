from asyncio import sleep
from datetime import datetime
import logging

import discord
from discord import Embed, Color, Message
from discord.ext import commands

from Database.DiscordEvent import DiscordEvent


class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await sleep(1)
        event_dict = {
            'event': 'member_join',
            'member_id': str(member.id),
            'member_name': member.name,
            'member_global_name': member.global_name,
            'member_nick': member.nick,
            'member_roles': [role.id for role in member.roles],
            'joined_at': member.joined_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'created_at': member.created_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f'),
        }
        await self.log_event(event_dict)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await sleep(1)
        # Check if the member was kicked or banned
        event_dict = None
        async for entry in member.guild.audit_logs(limit=1, user=member):
            if entry.action == discord.AuditLogAction.kick:
                event_dict = {
                    'event': 'member_kick',
                    'member_id': str(member.id),
                    'reason': entry.reason,
                }
            elif entry.action == discord.AuditLogAction.ban:
                event_dict = {
                    'event': 'member_ban',
                    'member_id': str(member.id),
                    'reason': entry.reason
                }
            else:
                event_dict = {
                    'event': 'member_leave',
                    'member_id': str(member.id),
                }
            event_dict['left_at'] = entry.created_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f')
        await self.log_event(event_dict)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await sleep(1)
        event_dict = {
            'event': 'member_update',
            'member_id': str(after.id),
            'updated_at': datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f'),
        }
        updated = False
        if before.name != after.name:
            event_dict['name_before'] = before.name
            event_dict['name_after'] = after.name
            updated = True
        if before.global_name != after.global_name:
            event_dict['global_name_before'] = before.global_name
            event_dict['global_name_after'] = after.global_name
            updated = True
        if before.nick != after.nick:
            event_dict['nick_before'] = before.nick
            event_dict['nick_after'] = after.nick
            updated = True
        if before.roles != after.roles:
            event_dict['roles_added'] = [role.id for role in after.roles if role not in before.roles]
            event_dict['roles_removed'] = [role.id for role in before.roles if role not in after.roles]
            updated = True
        # Check if member was updated by a mod
        async for entry in after.guild.audit_logs(limit=1, user=after):
            event_dict['updated_by'] = str(entry.user.id)
            event_dict['reason'] = entry.reason
        if updated:
            await self.log_event(event_dict)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await sleep(1)
        if message.author.bot:
            return
        # Add event to database
        event_dict = {
            'event': 'message_create',
            'message_id': str(message.id),
            'member_id': str(message.author.id),
            'channel_id': str(message.channel.id),
            'content': message.content,
            'created_at': message.created_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'attachments': [attachment.url for attachment in message.attachments],
        }
        if message.reference:
            event_dict['reference'] = str(message.reference.message_id)
        await self.log_event(event_dict)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await sleep(1)
        if message.author.bot:
            return
        event_dict = {
            'event': 'message_delete',
            'message_id': str(message.id),
            'member_id': str(message.author.id),
            'channel_id': str(message.channel.id),
            'content': message.content,
            'attachments': [attachment.url for attachment in message.attachments],
            'deleted_at': message.created_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f'),
        }
        # Check if the message was deleted by a mod
        async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            if entry.target.id == message.author.id:
                event_dict['deleted_by'] = str(entry.user.id)
                event_dict['reason'] = entry.reason
        await self.log_event(event_dict)

    @commands.Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        await sleep(1)
        if before.author.bot:
            return
        event_dict = {
            'event': 'message_edit',
            'message_id': str(after.id),
            'member_id': str(after.author.id),
            'channel_id': str(after.channel.id),
        }
        if after.edited_at:
            event_dict['edited_at'] = after.edited_at.astimezone().strftime('%Y-%m-%dT%H:%M:%S.%f')
        if before.content != after.content:
            event_dict['content_before'] = before.content
            event_dict['content_after'] = after.content
        if before.attachments != after.attachments:
            event_dict['attachments_before'] = [attachment.url for attachment in before.attachments]
            event_dict['attachments_after'] = [attachment.url for attachment in after.attachments]
        await self.log_event(event_dict)

    async def log_event(self, event_dict: dict):
        try:
            # Generate a unique ID for the event
            id_key = 'message_id' if 'message_id' in event_dict else 'member_id'
            timestamp = event_dict.get('created_at', event_dict.get('updated_at', event_dict.get('deleted_at', event_dict.get( 'edited_at', ''))))            # Define event colors
            timestamp = timestamp.replace('-', '').replace(':', '').replace('.', '')
            event_dict['id'] = f"{event_dict[id_key]}_{timestamp}"
            # Define event colors
            event_colors = {
                'member_join': Color.green(),
                'member_kick': Color.orange(),
                'member_ban': Color.red(),
                'member_leave': Color.dark_grey(),
                'member_update': Color.blue(),
                'message_create': Color.gold(),
                'message_delete': Color.dark_red(),
                'message_edit': Color.dark_orange(),
            }
            # Get the color based on the event, or default to white
            color = event_colors.get(event_dict['event'], Color.default())
            embed = Embed(title=event_dict['event'], color=color)
            # For each key in the dict, add a field to the embed
            for key in event_dict:
                if key == 'event':
                    continue
                elif key == 'channel_id':
                    embed.add_field(name='Channel', value=f"<#{event_dict[key]}> ({event_dict[key]})", inline=True)
                elif key == 'message_id':
                    embed.add_field(name='Message', value=f"[Jump to message](https://discord.com/channels/{self.client.settings.guild.id}/{event_dict['channel_id']}/{event_dict[key]})", inline=True)
                elif key == 'member_id':
                    embed.add_field(name='Member', value=f"<@{event_dict[key]}> ({event_dict[key]})", inline=True)
                elif key == 'updated_by':
                    embed.add_field(name='Updated By', value=f"<@{event_dict[key]}> ({event_dict[key]})", inline=True)
                elif key == 'deleted_by':
                    embed.add_field(name='Deleted By', value=f"<@{event_dict[key]}> ({event_dict[key]})", inline=True)
                elif 'attachments' in key:
                    # Mask the URL as the embed file name
                    embed.add_field(name='Attachments', value="\n".join([f"[{attachment.split('/')[-1]}]({attachment})" for attachment in event_dict[key]]), inline=False)
                elif 'roles' in key:
                    embed.add_field(name=key.replace('_', ' '), value="\n".join([f"<@&{role}>" for role in event_dict[key]]), inline=False)
                elif 'at' in key:
                    # Convert datetime to unix timestamp
                    timestamp_str = event_dict[key]
                    dt_object = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
                    unix_time = int(dt_object.timestamp())
                    # Post datetime as discord timestamp
                    embed.add_field(name=key.replace('_', ' '), value=f"<t:{unix_time}:f>", inline=False)
                else:
                    embed.add_field(name=key.replace('_', ' '), value=event_dict[key], inline=False)

            # Post the embed to the log channel, ignoring message create events
            if event_dict['event'] != 'message_create':
                await self.client.settings.log_channel.send(embed=embed)
            # Add the event to the database
            await DiscordEvent(self.client.database).add_event(event_dict)
        except Exception as e:
            logging.getLogger("AuditLog").error(f"EventData:{event_dict}\n\nError:{e}")

async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
