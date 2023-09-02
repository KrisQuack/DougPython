import os
import random

import discord
from discord import app_commands, ui, Embed, File
from discord.ext import commands


class Verify(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="verifysetup", description="Setup the verification system")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        embed = Embed(title="Verification System", description=(
            "To verify you are not a bot please click the **Verify** button below. "
            "You will be sent an image with a random number of bell peppers. "
            "Click the **Submit** button under the image and enter the number of bell peppers "
            "you saw in the image. If you are not a bot you will be verified."
        ))
        await interaction.response.send_message(embed=embed,
                                                components=[ui.Button(label="Verify", custom_id="verifyrequest")])

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.Interaction):
        if interaction.custom_id == "verifyrequest":
            files = os.listdir("Media/Verify")
            file = random.choice(files)
            file_name, _ = os.path.splitext(file)

            await interaction.response.send_message(
                file=File(f"Media/Verify/{file}", filename=f"verify{interaction.user.id}.jpeg"),
                components=[
                    ui.Button(style=ui.ButtonStyle.PRIMARY, label="Submit", custom_id=f"verifyresponse:{file_name}")],
                ephemeral=True
            )

        elif interaction.custom_id.startswith("verifyresponse:"):
            _, file_name = interaction.custom_id.split(":")
            await interaction.response.send_modal(VerifyModal(file_name=file_name))


class VerifyModal(ui.Modal):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name

    peppers = ui.TextInput(label="Peppers", placeholder="Please enter the amount of bell peppers you saw in the image")

    async def on_submit(self, interaction: discord.Interaction):
        if self.peppers == self.file_name:
            await interaction.followup.send("You are not a bot!", ephemeral=True)
        else:
            await interaction.followup.send("You are a bot!", ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Verify(self))
