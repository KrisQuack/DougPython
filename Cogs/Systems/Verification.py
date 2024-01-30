import logging
import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from Classes.DiscordFunctions.ModActions import Timeout_User
from Classes.Database.Members import get_member, update_member


class Verification(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.check_verification.start()
        self.onboarding = self.client.get_channel(1041406855123042374)
        self.new_role = self.client.guilds[0].get_role(935020318408462398)
        self.member_role = self.client.guilds[0].get_role(720807137319583804)

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

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.onboarding.send(f"{member.mention} please complete the verification above", delete_after=60)

    @tasks.loop(minutes=5)
    async def check_verification(self):
        try:
            graduated = 0
            kicked = 0
            deleted_messages = 0
            # Assign variables
            ten_minutes_ago = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=60))
            one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
            # Loop through all members in the server who do not have the member role
            for member in self.client.guilds[0].members:
                # If the member does not have the member role
                if self.member_role in member.roles:
                    continue
                # If the member is not a bot and does not have the new role
                if not member.bot and self.new_role not in member.roles:
                    # If the member has been in the server for more than 10 minutes
                    if member.joined_at < ten_minutes_ago:
                        # Kick the member for not being verified
                        await member.kick(reason="Not verified")
                        kicked += 1
                    else:
                        # Send the member a reminder to verify
                        await self.onboarding.send(
                            f"{member.mention} you have not yet verified and will be kicked in the next 5 minutes if not complete",
                            delete_after=60)
                # If the member has been in the server for more than one week and has the new role
                elif member.joined_at < one_week_ago and self.new_role in member.roles:
                    # Assign the member role to the member
                    await member.add_roles(self.member_role, reason="Graduated")
                    graduated += 1
            # Check if there are any messages in the onboarding channel older than 10 minutes
            messages = [msg async for msg in self.onboarding.history(limit=100, before=ten_minutes_ago)]
            for message in messages:
                # If it is not the verification message
                if message.id != 1158902786524721212:
                    await message.delete()
                    deleted_messages += 1
            if graduated > 0 or kicked > 0 or deleted_messages > 0:
                logging.getLogger('Verification').info(f"Verification check complete: {graduated} graduated, {kicked} kicked, {deleted_messages} messages deleted")
        except Exception as e:
            logging.getLogger("Verification").error(f"Failed to check verification: {e}")

    @check_verification.before_loop
    async def before_check_verification(self):
        await self.client.wait_until_ready()


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.blurple, emoji="✔️", custom_id="verify")
    async def verify_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # List all JPEG files in the 'Data/Verification' directory
            jpeg_files = [f for f in os.listdir('Data/Verification') if f.endswith('.jpg')]
            # Randomly select one JPEG file from the list
            selected_file = random.choice(jpeg_files)
            # Extract the number (which serves as the answer) from the selected file's name
            answer = int(os.path.splitext(selected_file)[0].split('_')[-1])
            # Store the answer in the database
            dbUser = await get_member(interaction.user, interaction.client.database)
            dbUser['verification'] = answer
            await update_member(dbUser, interaction.client.database)
            # Create a Discord File object using the path to the selected JPEG file
            image = discord.File(os.path.join('Data/Verification', selected_file), f'{interaction.user.id}.jpg')
            # Send a message along with the randomly selected image and associated view for verification
            await interaction.response.send_message("## How many bell peppers do you see in the image above?",
                                                    view=VerifyAnswerView(), ephemeral=True, file=image)
        except Exception as e:
            logging.getLogger("Verification").error(f"Failed to generate Verification for {interaction.user.name}: {e}")


class VerifyAnswerButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(style=discord.ButtonStyle.blurple, label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        option = int(self.label)
        view: VerifyAnswerView = self.view  # We're expecting the view to be an instance of VerifyAnswer
        await view.respond(interaction, option)


class VerifyAnswerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Create a list of numbers from 1 to 10
        numbers = list(range(1, 11))
        # Shuffle the list
        random.shuffle(numbers)
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
        try:
            # Get the answer from the database
            dbUser = await get_member(interaction.user, interaction.client.database)
            answer = dbUser['verification']
            if option == answer:
                dbUser['verification'] = None
                await update_member(dbUser, interaction.client.database)
                role = interaction.guild.get_role(935020318408462398)
                await interaction.user.add_roles(role, reason="Verified")
                # If the user account is created less than one week, time out for the remainder of the week
                safe_age = interaction.user.created_at + timedelta(weeks=1)
                if safe_age > datetime.utcnow().replace(tzinfo=timezone.utc):
                    time_remaining = interaction.user.created_at + timedelta(weeks=1) - datetime.utcnow().replace(tzinfo=timezone.utc)
                    await Timeout_User(interaction.user, time_remaining, "Your account must be at least one week old to interact with the server")
                    await interaction.response.send_message("Correct! You are now freshman however you must wait untill your account is one week old to interact", ephemeral=True)
                else:
                    await interaction.response.send_message("Correct! You are now freshman", ephemeral=True)
            else:
                await interaction.response.send_message("Incorrect!", ephemeral=True)
        except Exception as e:
            logging.getLogger("Verification").error(f"Failed to verify {interaction.user.name}: {e}")


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Verification(self))
    self.add_view(VerifyButton())