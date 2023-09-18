import discord
from discord import AutoModAction, Embed, Color
from discord.ext import commands
import re

from Database.BotSettings import BotSettings

class AutoMod(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_automod_action(self, action: AutoModAction):
        ## Deez Nutz ##
        if action.rule_id == 1119010971290189946:
            # Get users message history
            guild = await BotSettings.get_guild(self.client)
            member = guild.get_member(action.user_id)
            # Get timestamp for one week ago
            one_week_ago = action.timestamp - discord.Duration(weeks=1)
            messages = [msg async for msg in member.history(limit=10000, after=one_week_ago)]
            print(f"Deez Nutz ({len(messages)} messages) - {member.name} ({member.id})")
            # Count messages that match regex
            regex = action.matched_keyword
            count = 0
            async for message in messages:
                if re.search(regex, message.content):
                    count += 1
            # Time out the user based on the count, incrementing hours like 1,2,4,8
            hours = 2 ** count
            print(f"Deez Nutz ({count} matches) - {member.name} ({member.id}) - {hours} hours")
            # await member.timeout(hours=hours, reason=f"Deez Nutz ({count} matches)")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoMod(self))
