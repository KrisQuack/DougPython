import re
import logging
from asyncio import sleep

import discord
from discord import TextChannel
from discord.ext import commands

import re

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
        
        # AttachmentsAutomod
        await self.AttachmentsAutomod(message)
        
        

    @commands.Cog.listener()
    async def on_message_edit(self, before, after: discord.Message):
        # Check if the message is from a bot, mod or DM
        if after.guild is None or after.author.bot or after.author.guild_permissions.moderate_members:
            return

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.ForumAutomod(thread)

    async def AutoPublish(self, message: discord.Message):
        # If channel is an announcement channel
        channel: TextChannel = message.channel
        if channel.type == discord.ChannelType.news:
            # publish message
            await message.publish()

    async def ForumAutomod(self, thread: discord.Thread):
        try:
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
        except Exception as e:
            logging.getLogger("ForumAutomod").error(f"Failed to pin thread: {e}")
    
    async def AttachmentsAutomod(self, message: discord.Message):
        # Check if the message has attachments
        if message.attachments:
            for attachment in message.attachments:
                # Check if the attachment file name ends with .zip, .exe, or .msi
                if re.search(r"\.(zip|rar|7z|tar|gz|iso|dmg|exe|msi|apk)$", attachment.filename, re.IGNORECASE):
                    # Alert the mod team
                    embed = discord.Embed(
                        title="Prohibited Attachment",
                        description="A prohibited attachment has been detected and removed.",
                        color=discord.Color.red(),
                        url=message.jump_url,
                        timestamp=message.created_at
                    )
                    embed.add_field(name="Attachments", value="\n".join([f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments]))
                    embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.display_avatar.url)
                    channel = message.guild.get_channel(755155718214123600)
                    await channel.send(embed=embed)
                    # Notify the user
                    await message.reply("Please do not upload zip files or executables, the mod team has no way to verify these are not malicious without investing significant time to investigate each upload.", delete_after=30)
                    # Delete the message
                    await message.delete()
                    break
                
async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoMod(self))
