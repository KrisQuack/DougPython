import discord
from discord import Embed, Color
from discord.ext import commands

from Database.BotSettings import BotSettings

class DMRelay(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if the message is from a DM channel and not from the bot itself
        if isinstance(message.channel, discord.DMChannel) and message.author != self.client.user:
            # Create the main embed
            embed = Embed(description=message.content, color=Color.blue())  # Using blue as a placeholder for color
            embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.avatar.url)
            embed.timestamp = message.created_at

            # If there are attachments, add them to the embed
            attachment_embeds = []
            for attachment in message.attachments:
                attach_embed = Embed(title=attachment.filename, url=attachment.url,
                                     color=Color.blue())  # Using blue as a placeholder for color
                attach_embed.set_image(url=attachment.url)
                attach_embed.set_author(name=f"{message.author.name} ({message.author.id})",
                                        icon_url=message.author.avatar.url)
                attach_embed.timestamp = message.created_at
                attachment_embeds.append(attach_embed)

            # Send the main embed and any attachment embeds to the specified channel
            dmChannel = await BotSettings.get_dm_receipt_channel(self.client)
            await dmChannel.send(embed=embed)
            for attach_embed in attachment_embeds:
                await dmChannel.send(embed=attach_embed)
            await message.channel.send("Message sent to the mods!")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(DMRelay(self))
