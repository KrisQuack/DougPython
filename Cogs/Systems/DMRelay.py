import discord
from discord import Embed, Color
from discord.ext import commands


class DMRelay(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if the message is from a DM channel and not from the bot itself
        if isinstance(message.channel, discord.DMChannel) and message.author != self.client.user:
            # Create the main embed
            embed = Embed(description=message.content, color=Color.blue())  # Using blue as a placeholder for color
            embed.set_author(name=f"{message.author.name} ({message.author.id})",
                             icon_url=message.author.display_avatar.url)
            embed.timestamp = message.created_at

            # If there are attachments, add them to the embed
            attachment_embeds = []
            for attachment in message.attachments:
                attach_embed = Embed(title=attachment.filename, url=attachment.url,
                                     color=Color.blue())  # Using blue as a placeholder for color
                attach_embed.set_image(url=attachment.url)
                attach_embed.set_author(name=f"{message.author.name} ({message.author.id})",
                                        icon_url=message.author.display_avatar.url)
                attach_embed.timestamp = message.created_at
                attachment_embeds.append(attach_embed)

            # Send the main embed and any attachment embeds to the specified channel
            dmChannel: discord.TextChannel = self.client.statics.dm_receipt_channel
            await dmChannel.send(embed=embed, view=DMHistoryView())
            for attach_embed in attachment_embeds:
                await dmChannel.send(embed=attach_embed)
            await message.channel.send(
                "This message has been sent to the mod team and they will respond when avaliable. Please only DM if you have serious questions or concerns. Abusing this service will result in removal from the server",
                delete_after=30)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Check if the message is from a DM channel and not from the bot itself
        if isinstance(after.channel, discord.DMChannel) and after.author != self.client.user:
            # Create the main embed
            embed = Embed(title="DM Edited", color=Color.yellow())  # Using blue as a placeholder for color
            embed.set_author(name=f"{after.author.name} ({after.author.id})",
                             icon_url=after.author.display_avatar.url)
            embed.timestamp = after.created_at
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)

            # Send the main embed to the specified channel
            dmChannel: discord.TextChannel = self.client.statics.dm_receipt_channel
            await dmChannel.send(embed=embed, view=DMHistoryView())

class DMHistoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="View DM History (last 20)", style=discord.ButtonStyle.blurple, custom_id="dmhistory")
    async def history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        # Get the embed from the message
        embed = interaction.message.embeds[0]
        member_id = int(embed.author.name.split("(")[1].split(")")[0])
        member = await interaction.client.fetch_user(member_id)
        # Get the DM channel
        dm_channel = await member.create_dm()
        # Get the messages
        messages = [msg async for msg in dm_channel.history(limit=20)]
        messages.reverse()
        # Create the string for the messages
        messageStr = ""
        for msg in messages:
            author_name = msg.author.name
            content = msg.clean_content
            if msg.embeds:
                for embed in msg.embeds:
                    if embed.description:
                        content += f" {embed.description}"
            messageStr += f"- {author_name}: {content}\n"
        # Get the last 4000 characters
        messageStr = messageStr[-4000:]
        # Create an embed with the messages
        historyEmbed = Embed(title="DM History", description=messageStr, color=Color.orange())
        # Send the embed
        await interaction.followup.send(embed=historyEmbed, ephemeral=True)
        


async def setup(self: commands.Bot) -> None:
    await self.add_cog(DMRelay(self))
    self.add_view(DMHistoryView())
