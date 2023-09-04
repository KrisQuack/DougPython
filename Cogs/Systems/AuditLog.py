import discord
from discord import Embed, Color
from discord.ext import commands


class AuditLog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = Embed(title="User Joined", color=Color.green())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = Embed(title="User Left", color=Color.red())
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        embed = Embed(title="Member Updated", color=Color.orange())
        if before.nick != after.nick:
            embed.add_field(name="Nickname", value=f"{before.nick} -> {after.nick}", inline=False)
        embed.set_author(name=f"{after.name} ({after.id})", icon_url=after.avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.DMChannel):
            return
        embed = Embed(title=f"Message Deleted in {message.channel.name}", color=Color.red())
        embed.add_field(name="Content", value=message.content, inline=False)
        embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.avatar.url)
        await self.client.settings.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(after.channel, discord.DMChannel):
            return
        if before.content == after.content:
            return
        embed = Embed(title=f"Message Edited in {before.channel.name}", color=Color.orange())
        embed.add_field(name="Before", value=before.content, inline=False)
        embed.add_field(name="After", value=after.content, inline=False)
        embed.set_author(name=f"{before.author.name} ({before.author.id})", icon_url=before.author.avatar.url)
        await self.client.settings.log_channel.send(embed=embed)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(AuditLog(self))
