import discord
from discord.ext import commands
from discord import app_commands

class PinUnpin(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.pin_message = app_commands.ContextMenu(
            name='Forum: Pin',
            callback=self.pin_message,
        )
        self.unpin_message = app_commands.ContextMenu(
            name='Forum: UnPin',
            callback=self.unpin_message,
        )
        self.client.tree.add_command(self.pin_message)
        self.client.tree.add_command(self.unpin_message)

    async def pin_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        # Check if the channel is a thread
        if isinstance(message.channel, discord.Thread):
            # Get the first pinned message based on creation time
            pinned_messages = await message.channel.pins()
            first_pinned_message = min(pinned_messages, key=lambda m: m.created_at, default=None)

            # Check if the user is the owner of the first pinned message
            if first_pinned_message and first_pinned_message.author.id == interaction.user.id:
                await message.pin()
                await interaction.followup.send("Message pinned", ephemeral=True)
                return

        await interaction.followup.send("This command can only be used in threads you own", ephemeral=True)

    async def unpin_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        # Check if the channel is a thread
        if isinstance(message.channel, discord.Thread):
            # Get the first pinned message based on creation time
            pinned_messages = await message.channel.pins()
            first_pinned_message = min(pinned_messages, key=lambda m: m.created_at, default=None)

            # Check if the user is the owner of the first pinned message and message is not the first pinned
            if first_pinned_message and first_pinned_message.author.id == interaction.user.id and message.id != first_pinned_message.id:
                await message.unpin()
                await interaction.followup.send("Message unpinned", ephemeral=True)
                return

        await interaction.followup.send("This command can only be used in threads you own and not on the first message", ephemeral=True)

async def setup(self: commands.Bot) -> None:
    await self.add_cog(PinUnpin(self))
