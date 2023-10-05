import datetime
import logging
import re

from discord import AutoModAction
from discord.ext import commands


class AutoMod(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_automod_action(self, action: AutoModAction):
        return # Disable automod
        ## Deez Nutz ##
        if action.rule_id == 1119010971290189946:
            pass


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AutoMod(self))
