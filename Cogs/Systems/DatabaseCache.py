import discord
from discord.ext import commands


class DatabaseCache(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == 130062174918934528 and message.content == "cache":
            print(message)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(DatabaseCache(self))
