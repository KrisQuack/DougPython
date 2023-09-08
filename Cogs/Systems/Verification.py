import os
import random

import discord
from discord import app_commands
from discord.ext import commands


class Verification(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="verificationsetup")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def VerificationSetup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Verification",
            description=f"To verify click the button below, you will be shown an image and asked to select how many bell peppers you see in the image.",
            color=discord.Color.dark_purple()
        )
        # Send the embed
        await interaction.channel.send(embed=embed, view=VerifyButton())


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verify")
    async def verify_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # List all JPEG files in the 'Data/Verification' directory
        jpeg_files = [f for f in os.listdir('Data/Verification') if f.endswith('.jpeg')]
        # Randomly select one JPEG file from the list
        selected_file = random.choice(jpeg_files)
        # Extract the number (which serves as the answer) from the selected file's name
        answer = int(os.path.splitext(selected_file)[0])
        # Create a Discord File object using the path to the selected JPEG file
        image = discord.File(os.path.join('Data/Verification', selected_file), f'{interaction.user.id}.jpeg')
        # Send a message along with the randomly selected image and associated view for verification
        await interaction.response.send_message("## How many bell peppers do you see in the image below?",
                                                view=VerifyAnswerView(answer), ephemeral=True, file=image)


class VerifyAnswerButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(style=discord.ButtonStyle.blurple, label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        option = int(self.label)
        view: VerifyAnswerView = self.view  # We're expecting the view to be an instance of VerifyAnswer
        await view.respond(interaction, option)


class VerifyAnswerView(discord.ui.View):
    def __init__(self, answer):
        super().__init__(timeout=None)
        self.answer = answer
        numbers = list(range(1, 11))  # Create a list of numbers from 1 to 10
        random.shuffle(numbers)  # Shuffle the numbers
        # Define some colors you'd like to use
        colors = [
            discord.ButtonStyle.blurple,
            discord.ButtonStyle.grey,
            discord.ButtonStyle.green,
            discord.ButtonStyle.red
        ]

        for num in numbers:
            color = random.choice(colors)  # Pick a random color
            button = VerifyAnswerButton(label=str(num), custom_id=f"verify_answer_{num}")
            button.style = color  # Set the button color
            self.add_item(button)

    async def respond(self, interaction: discord.Interaction, option: int):
        if option == self.answer:
            await interaction.response.send_message("Correct!", ephemeral=True)
        else:
            await interaction.response.send_message("Incorrect!", ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Verification(self))
    self.add_view(VerifyButton())
