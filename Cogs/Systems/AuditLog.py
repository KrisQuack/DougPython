import discord
from discord import Embed, Color
from discord.ext import commands

class AuditLog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = Embed(title="User Joined", color=Color.green())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = Embed(title="User Left", color=Color.red())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        embed = Embed(title="Member Updated", color=Color.orange())
        if before.nick != after.nick:
            embed.add_field(name="Nickname", value=f"{before.nick} -> {after.nick}", inline=False)
        if before.roles != after.roles:
            # List what roles were added and removed
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            if added_roles:
                embed.add_field(name="Roles Added", value=", ".join([role.mention for role in added_roles]))
            if removed_roles:
                embed.add_field(name="Roles Removed", value=", ".join([role.mention for role in removed_roles]))
        embed.set_author(name=f"{after.name} ({after.id})", icon_url=after.display_avatar.url)
        if embed.fields:
            await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            return

        # Create the main embed for the deleted message
        main_embed = Embed(title=f"Message Deleted in {message.channel.name}", color=Color.red())
        main_embed.add_field(name="Content", value=message.content, inline=False)
        main_embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.display_avatar.url)

        # List to hold all the embeds
        all_embeds = [main_embed]

        # Add attachments as separate embeds to the list
        for attachment in message.attachments:
            attachment_embed = Embed(title=f"Attachment from {message.author.name}", color=Color.red())
            attachment_embed.set_image(url=attachment.url)
            all_embeds.append(attachment_embed)

        # Send all embeds in one go
        await self.client.settings.log_channel.send(embeds=all_embeds)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(after.channel, discord.DMChannel):
            return
        if before.content == after.content:
            return
        embed = Embed(title=f"Message Edited in {before.channel.name}", color=Color.orange())
        embed.url = after.jump_url
        embed.add_field(name="Before", value=before.content, inline=False)
        embed.add_field(name="After", value=after.content, inline=False)
        embed.set_author(name=f"{before.author.name} ({before.author.id})", icon_url=before.author.display_avatar.url)
        await self.client.settings.log_channel.send(embed=embed)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
