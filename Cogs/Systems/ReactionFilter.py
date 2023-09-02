from discord.ext import commands, tasks


class ReactionFilter(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.reaction_filter.start()  # Start the background task

    @tasks.loop(minutes=1)  # Run this loop every 5 minutes
    async def reaction_filter(self):
        # Assuming you have a list of whitelisted emote names
        emote_whitelist = self.client.settings.reaction_filter_emotes

        for channel in self.client.settings.reaction_filter_channels:
            if channel is None:
                continue

            messages = [msg async for msg in channel.history(limit=20)]
            for message in messages:
                for reaction in message.reactions:
                    if str(reaction.emoji) not in emote_whitelist:
                        await message.clear_reaction(reaction.emoji)

    @reaction_filter.before_loop
    async def before_reaction_filter(self):
        await self.client.wait_until_ready()  # Wait until the bot logs in


async def setup(client):
    await client.add_cog(ReactionFilter(client))
