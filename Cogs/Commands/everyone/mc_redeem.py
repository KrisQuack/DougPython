import random

import discord
from discord import app_commands
from discord.ext import commands

from Classes.Database.Members import get_member, update_member


class Minecraft(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="mc_redeem", description="Get a Twitch redemption code for Minecraft")
    @app_commands.guild_only()
    async def redeem(self, interaction: discord.Interaction):
        # Generate a random series of characters
        random_part = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(5))
        code = f'DMC-{random_part}'
        # Add the code to the database
        dbUser = await get_member(interaction.user, self.client.database)
        dbUser['mc_redeem'] = code
        await update_member(dbUser, self.client.database)
        # Send the code to the user
        await interaction.response.send_message(f"Your code is: **{code}**\nUse this in the Twitch redemption box",
                                                ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Minecraft(self))
