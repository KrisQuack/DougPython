import discord
from discord import Message, TextChannel 
from discord.ext import commands

class AutoPublish(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # If channel is an announcement channel
        channel: TextChannel = message.channel
        if channel.type == discord.ChannelType.news:
            # publish message
            await message.publish()

async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoPublish(self))
