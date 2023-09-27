import discord
from discord import app_commands, Embed
from discord.ext import commands

class SendDM(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="send_dm", description="Send a DM to a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        user="The user to send the DM to",
        message="The message to send to the user"
    )
    async def send_dm(self, interaction: discord.Interaction, user: discord.Member, message: str):
        # Create the embed for the user
        user_embed = Embed(description=message, color=discord.Color.orange())
        user_embed.set_author(name=f"{interaction.guild.name} Mods", icon_url=interaction.guild.icon.url)
        user_embed.set_footer(text="Any replies to this DM will be sent to the mod team")
        user_embed.timestamp = interaction.created_at

        # Send the DM
        await user.send(embed=user_embed)

        # Create the receipt embed for the mod team
        mod_embed = Embed(description=message, color=discord.Color.orange())
        mod_embed.set_author(name=f"DM to {user.name} ({user.id}) from {interaction.user.name}",
                             icon_url=interaction.user.display_avatar.url)
        mod_embed.timestamp = interaction.created_at

        # Assuming you have a way to get the DM receipt channel (replace with your method)
        await self.client.settings.dm_receipt_channel.send(embed=mod_embed)
        await interaction.response.send_message("DM Sent", ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(SendDM(self))
