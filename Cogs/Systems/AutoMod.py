import datetime
import re

from discord import AutoModAction
from discord.ext import commands

from Database.DiscordEvent import DiscordEvent

class AutoMod(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_automod_action(self, action: AutoModAction):
        ## Deez Nutz ##
        if action.rule_id == 1119010971290189946:
            # Get users message history
            guild = self.client.settings.guild
            member = guild.get_member(action.user_id)
            # Get timestamp for one week ago
            databaseEvents = DiscordEvent(self.database).get_all_events_by_key('member_id', str(member.id))
            databaseEventsList = [item async for item in databaseEvents]
            # Only keep events with event as message_create
            databaseEventsList = [item for item in databaseEventsList if item['event'] == 'message_create']
            print(f"Deez Nutz ({len(databaseEventsList)} messages) - {member.name} ({member.id})")
            # Count messages that match regex
            regex = action.matched_keyword
            count = 0
            for message in databaseEventsList:
                if re.search(regex, message.content):
                    count += 1
            # Time out the user based on the count, incrementing hours like 1,2,4,8
            hours = 2 ** count
            print(f"Deez Nutz ({count} matches) - {member.name} ({member.id}) - {hours} hours")
            # await member.timeout(hours=hours, reason=f"Deez Nutz ({count} matches)")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoMod(self))
