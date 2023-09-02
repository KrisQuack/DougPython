import aiohttp
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

class Move(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="move", description="Move a message to another channel")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        message_id="The ID of the message to move",
        channel="The channel to move the message to"
    )
    async def move(self, interaction: discord.Interaction, message_id: str, channel: discord.TextChannel):
        await interaction.response.defer()
        # Identify if it's a thread
        if isinstance(channel, discord.Thread):
            channel = channel.parent

        # Fetch the message to move
        source_channel = interaction.channel
        try:
            message_to_move = await source_channel.fetch_message(message_id)
        except discord.NotFound:
            await interaction.followup.send("Message not found")
            return

        # Create or find a webhook in the target channel
        webhooks = await channel.webhooks()
        webhook = next((wh for wh in webhooks if wh.name == "Wahaha"), None)
        if webhook is None:
            webhook = await channel.create_webhook(name="Wahaha")

        # Prepare content
        author = message_to_move.author
        content = message_to_move.content
        username = author.display_name
        avatar_url = author.avatar.url if author.avatar else None

        # Handle attachments
        if message_to_move.attachments:
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_attachment(session, at.url) for at in message_to_move.attachments]
                attachments = await asyncio.gather(*tasks)
                files = [discord.File(a[0], filename=a[1]) for a in attachments]
                await webhook.send(content=content, username=username, avatar_url=avatar_url,
                                   embeds=message_to_move.embeds, files=files)
        else:
            await webhook.send(content=content, username=username, avatar_url=avatar_url, embeds=message_to_move.embeds)

        await message_to_move.delete()
        await interaction.followup.send(f"{author.mention} your message has been moved to {channel.mention}")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Move(self))

async def fetch_attachment(session, url):
    async with session.get(url) as resp:
        assert resp.status == 200
        return await resp.read(), url.split("/")[-1]
