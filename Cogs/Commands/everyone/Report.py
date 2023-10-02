import discord
from discord import app_commands, ui, Embed
from discord.ext import commands


class Report(commands.GroupCog, name="report", description="Report a user or message"):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.report_user = app_commands.ContextMenu(
            name='Report: User',
            callback=self.report_user,
        )
        self.report_user.guild_only = True
        self.report_message = app_commands.ContextMenu(
            name='Report: Message',
            callback=self.report_message,
        )
        self.report_message.guild_only = True
        self.client.tree.add_command(self.report_user)
        self.client.tree.add_command(self.report_message)

    @app_commands.command(name="user", description="Report a user")
    @app_commands.guild_only()
    async def report_user_command(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_modal(ReportModal(self.client, user=user))

    async def report_user(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_modal(ReportModal(self.client, user=user))

    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(ReportModal(self.client, user=message.author, message=message))


class ReportModal(ui.Modal, title="Report"):
    def __init__(self, client: commands.Bot, user: discord.Member, message: discord.Message = None):
        super().__init__()
        self.user = user
        self.message = message
        self.client = client

    reason = ui.TextInput(label="Reason", placeholder="Enter a reason for the report",
                          style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embeds = []
        if self.message:
            embed = Embed(title="Message Reported")
            embed.url = self.message.jump_url
            embed.add_field(name="User Info",
                            value=f"\nMention: {self.message.author.mention}\nUsername: {self.message.author.name}\nID: {self.message.author.id}",
                            inline=False)
            embed.add_field(name="Message Info",
                            value=f"\nChannel: {self.message.channel.mention}\nMessage: {self.message.content}",
                            inline=False)
            embed.add_field(name="Reason", value=self.reason,
                            inline=False)
            embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})",
                             icon_url=interaction.user.display_avatar.url)
            embed.timestamp = interaction.created_at
            embeds.append(embed)

            for attachment in self.message.attachments:
                attach_embed = Embed(title="Attachment")
                attach_embed.set_image(url=attachment.url)
                attach_embed.timestamp = interaction.created_at
                embeds.append(attach_embed)
        else:
            embed = Embed(title="User Reported")
            embed.add_field(name="User Info",
                            value=f"\nMention: {self.user.mention}\nUsername: {self.user.name}\nID: {self.user.id}",
                            inline=False)
            embed.add_field(name="Reason", value=self.reason, inline=False)
            embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})",
                             icon_url=interaction.user.display_avatar.url)
            embed.timestamp = interaction.created_at
            embeds.append(embed)
        try:
            await self.client.settings.report_channel.send(embeds=embeds)
            await interaction.response.send_message("Your report has been sent to the mods.", ephemeral=True)
        except Exception:
            await interaction.response.send_message(
                "An error occurred while submitting this request. Please try again or open a ticket.", ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Report(self))
