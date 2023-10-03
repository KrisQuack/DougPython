import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks


class Verification(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.check_verification.start()

    @app_commands.command(name="verificationsetup")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def VerificationSetup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description=f"""# Welcome to The Doug District!
Welcome abroad! Before you dive in, we need to make sure you're a human. It's as easy as 1-2!
## Step 1: Verification
Click the button below to embark on a mini quest where you'll be shown an image. Your mission is to **count the number of bell peppers in the image**. <:pepperCute:826963195242610700> Select the correct number below the image and you're one step closer to being *one of us!*
## Step 2: Enrollment
Now that you're verified (and probably craving some stuffed peppers), it’s time to personalize your journey. Select the **Channels & Roles** menu atop the channels list or click right here: <id:customize> to pick the roles that tickle your fancy. 
## Encountering Issues?
If you encounter any issues, fear not! Direct Message the {self.client.user.mention} bot with any details or screenshots of the issue at hand. We'll assist as soon as we can!

Once you're all set, the realm of The Doug District is yours to explore.""",
            color=discord.Color.dark_purple()
        )
        # Send the embed
        await interaction.channel.send(embed=embed, view=VerifyButton())
        # Respond to the interaction
        await interaction.response.send_message("Verification setup complete!", ephemeral=True)

    @tasks.loop(minutes=10)
    async def check_verification(self):
        # Assign variables
        ten_minutes_ago = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=10))
        one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
        new_role = self.client.guilds[0].get_role(935020318408462398)
        member_role = self.client.guilds[0].get_role(720807137319583804)
        # Loop through all members in the server who do not have the member role
        for member in self.client.guilds[0].members:
            # If the member does not have the member role
            if member_role in member.roles:
                continue
            # If the member is not a bot, joined more than 10 minutes ago, and does not have the new role
            if (not member.bot and
                    member.joined_at < ten_minutes_ago and
                    new_role not in member.roles):
                # Kick the member for not being verified
                await member.kick(reason="Not verified")
            # If the member has been in the server for more than one week and has the new role
            elif (member.joined_at < one_week_ago and new_role in member.roles):
                # Assign the member role to the member
                await member.add_roles(member_role, reason="Graduated")

    @check_verification.before_loop
    async def before_check_verification(self):
        await self.client.wait_until_ready()

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.blurple, emoji="✔️", custom_id="verify")
    async def verify_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # List all JPEG files in the 'Data/Verification' directory
        jpeg_files = [f for f in os.listdir('Data/Verification') if f.endswith('.jpg')]
        # Randomly select one JPEG file from the list
        selected_file = random.choice(jpeg_files)
        # Extract the number (which serves as the answer) from the selected file's name
        answer = int(os.path.splitext(selected_file)[0].split('_')[-1])
        # Create a Discord File object using the path to the selected JPEG file
        image = discord.File(os.path.join('Data/Verification', selected_file), f'{interaction.user.id}.jpg')
        # Send a message along with the randomly selected image and associated view for verification
        await interaction.response.send_message("## How many bell peppers do you see in the image above?",
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
            role = interaction.guild.get_role(935020318408462398)
            await interaction.user.add_roles(role, reason="Verified")
            await interaction.response.send_message("Correct! You are now freshman", ephemeral=True)
        else:
            await interaction.response.send_message("Incorrect!", ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Verification(self))
    self.add_view(VerifyButton())
