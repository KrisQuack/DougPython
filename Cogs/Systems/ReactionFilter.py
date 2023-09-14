import discord
from discord.ext import commands, tasks


class ReactionFilter(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ten_minute_loop.start()
        self.one_hour_loop.start()

    @tasks.loop(minutes=10)
    async def ten_minute_loop(self):
        await self.reaction_filter(10)

    @tasks.loop(minutes=60)
    async def one_hour_loop(self):
        await self.reaction_filter(100)

    async def reaction_filter(self, messageInt):
        try:
            # Assuming you have a list of whitelisted emote names
            emote_whitelist = self.client.settings.reaction_filter_emotes
            guild_emotes = self.client.settings.guild.emojis
            emote_whitelist += [emote.name for emote in guild_emotes]
            # Get the mod role from settings
            mod_role = self.client.settings.mod_role

            for channel in self.client.settings.reaction_filter_channels:
                if channel is None:
                    continue
                messages = [msg async for msg in channel.history(limit=messageInt)]
                for message in messages:
                    for reaction in message.reactions:\
                        # Check if the reaction is not whitelisted
                        if isinstance(reaction.emoji, discord.Emoji):
                            emoji_name = reaction.emoji.name
                        else:
                            emoji_name = reaction.emoji
                        if emoji_name not in emote_whitelist:
                            # Get all users who reacted with this emoji
                            users = [usr async for usr in reaction.users() if isinstance(usr, discord.Member)]
                            # Check if any user in the reaction is in the mod_role members list
                            if any(user in mod_role.members for user in users):
                                continue  # Skip this reaction if a user from the mod_role members list reacted
                            # Remove the reaction
                            await message.clear_reaction(reaction.emoji)
        except Exception as e:
            print(e)

    @ten_minute_loop.before_loop
    async def before_ten_minute_loop(self):
        await self.client.wait_until_ready()  # Wait until the bot logs in

    @one_hour_loop.before_loop
    async def before_one_hour_loop(self):
        await self.client.wait_until_ready()  # Wait until the bot logs in

async def setup(client):
    await client.add_cog(ReactionFilter(client))
