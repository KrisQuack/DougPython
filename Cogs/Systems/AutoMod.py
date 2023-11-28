import datetime
import logging
import re
from asyncio import sleep

import discord
from discord import TextChannel
from discord.ext import commands
from sqlalchemy.future import select

from Classes.Database.Message import query_messages, Message
from Classes.DiscordFunctions.ModActions import Timeout_User


class AutoMod(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if it is a DM
        if message.guild is None:
            return
        # Features that a bot or mod can trigger
        # AutoPublish
        await self.AutoPublish(message)
        # features that a bot or mod can't trigger
        if message.author.bot or message.author.guild_permissions.moderate_members:
            return
        # DeezNutz
        await self.DeezNutz(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after: discord.Message):
        # Check if the message is from a bot, mod or DM
        if after.guild is None or after.author.bot or after.author.guild_permissions.moderate_members:
            return
        # DeezNutz
        await self.DeezNutz(after)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.ForumAutomod(thread)

    async def AutoPublish(self, message: discord.Message):
        # If channel is an announcement channel
        channel: TextChannel = message.channel
        if channel.type == discord.ChannelType.news:
            # publish message
            await message.publish()

    async def DeezNutz(self, message: discord.Message):
        # Check if the message meets the regex
        pattern = r"((d[izse3]{2,})|(th[ozse3m]{2,}))\s*(nut|testicle)"
        if re.search(pattern, message.content, re.IGNORECASE):
            # Mark an eyes emote on the message
            await message.add_reaction('👀')
            # Check their last two weeks of messages
            messages = await query_messages(select(Message.content).where(Message.user_id == str(message.author.id),
                                                                          Message.created_at > datetime.datetime.utcnow() - datetime.timedelta(
                                                                              weeks=4)))
            messageList = [item async for item in messages]
            messageList = [item['content'] for item in messageList]
            # Count the number of times they've said deez nuts
            count = 0
            for msg in messageList:
                if re.search(pattern, msg, re.IGNORECASE):
                    count += 1
            # Time them out for the amount of times they have said it
            lengths = [1, 3, 6, 12, 24, 48, 72, 144]
            if count > 0:
                # Get the timeout length
                time_index = min(count - 1, len(lengths) - 1)
                timeout_hours = lengths[time_index]
                timeout = datetime.timedelta(hours=timeout_hours)
                await Timeout_User(message.author, timeout,
                                   'https://discord.com/channels/567141138021089308/880127379119415306/1119011566638080010')
                logging.info(
                    f"Timed out {message.author.display_name} for {timeout} for deez nuts\nMessage: {message.content}\n{message.jump_url}")

    async def ForumAutomod(self, thread: discord.Thread):
        if not isinstance(thread.parent, discord.ForumChannel):
            return
        # Pin the first message
        await sleep(1)
        # Get the first messages
        messages = [msg async for msg in thread.history(limit=5)]
        # Get the earliest message based on timestamp
        msg = sorted(messages, key=lambda msg: msg.created_at)[0]
        if msg:
            await msg.pin()
            # Create the embed
            embed = discord.Embed(
                title="Welcome to Your Thread!",
                description=(
                    "Server rules apply. Issues? Contact [mod team](https://discord.com/channels/567141138021089308/880127379119415306/1154847821514670160).\n"
                    f"<@{thread.owner_id}>: You can Pin/Unpin posts. [How?](https://cdn.discordapp.com/attachments/886548334154760242/1135511848817545236/image.png)"
                ),
                color=discord.Color.orange()
            )
            embed.set_author(name=thread.name, icon_url=thread.guild.icon.url)
            # Send the embed and pin it
            await thread.send(embed=embed)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoMod(self))
