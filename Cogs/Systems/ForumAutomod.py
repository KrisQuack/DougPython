import discord
from discord.ext import commands


class ThreadWelcomeCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        # Pin the first message
        await [msg async for msg in thread.history(limit=1)][0].pin()
        # Create the embed
        embed = discord.Embed(
            title="Welcome to your new thread!",
            description=(
                "Please remember the server rules still apply. "
                "If you have any issues, please contact the moderation team. "
                "More info: [here](https://discord.com/channels/567141138021089308/880127379119415306/1132052471481638932)\n"
                f"<@{thread.owner_id}> as the owner you may also Pin and Unpin posts in your thread, "
                "Just right click (hold down on mobile) on a message, select Apps and then Pin or Unpin. "
                "[Example](https://cdn.discordapp.com/attachments/886548334154760242/1135511848817545236/image.png)"
            ),
            color=discord.Color.orange()
        )
        embed.set_author(name=thread.name, icon_url=thread.guild.icon.url)
        # Send the embed and pin it
        await thread.send(embed=embed)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(ThreadWelcomeCog(self))
