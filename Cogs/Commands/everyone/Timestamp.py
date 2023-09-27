from datetime import datetime
import time
from typing import List

import discord
import pytz
from discord import app_commands, CategoryChannel
from discord.ext import commands, tasks


class Timestamp(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.date = '04/Jul/2000'
        self.update_time.start()

    @app_commands.command(name="timestamp", description="Convert a date and time to a Discord timestamp")
    @app_commands.guild_only()
    @app_commands.describe(
        date="The date to convert to a timestamp. Format: `04/Jul/2000`",
        time="The time to convert to a timestamp. Format: `18:00`",
        timezone="The time zone to use. Format: `America/Los_Angeles"
    )
    async def timestamp(self, interaction: discord.Interaction, date: str, time: str, timezone: str):
        # Check if the time zone is valid
        if timezone not in pytz.all_timezones:
            await interaction.response.send_message("Invalid time zone.", ephemeral=True)
            return

        # Create a date string using the provided date and time
        date_string = f"{date} {time}"

        # Convert to datetime object
        try:
            parsed_time = datetime.strptime(date_string, '%d/%b/%Y %H:%M')
        except ValueError:
            await interaction.response.send_message(
                "Invalid date or time format. Please use `04/Jul/2000` for date and `HH:MM` for time.", ephemeral=True)
            return

        # Apply the time zone
        tz = pytz.timezone(timezone)
        parsed_time = tz.localize(parsed_time)

        # Convert to Unix timestamp
        parsed_unix_time = int(parsed_time.timestamp())

        # Create Discord embed
        embed = discord.Embed(title="Time Stamp", color=discord.Color.blue())
        embed.add_field(name="Relative Time", value=f"`<t:{parsed_unix_time}:R>` : <t:{parsed_unix_time}:R>",
                        inline=False)
        embed.add_field(name="Absolute Time", value=f"`<t:{parsed_unix_time}:F>` : <t:{parsed_unix_time}:F>",
                        inline=False)
        embed.add_field(name="Short Date", value=f"`<t:{parsed_unix_time}:f>` : <t:{parsed_unix_time}:f>", inline=False)
        embed.add_field(name="Long Time", value=f"`<t:{parsed_unix_time}:T>` : <t:{parsed_unix_time}:T>", inline=False)
        embed.add_field(name="Short Time", value=f"`<t:{parsed_unix_time}:t>` : <t:{parsed_unix_time}:t>", inline=False)

        await interaction.response.send_message(content=f"<t:{parsed_unix_time}:t> <t:{parsed_unix_time}:R>",
                                                embed=embed, ephemeral=True)

    @timestamp.autocomplete('timezone')
    async def timezones_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        timezones = pytz.all_timezones
        if current == '':
            return [app_commands.Choice(name='America/Los_Angeles', value='America/Los_Angeles')]
        return [
            app_commands.Choice(name=timezone, value=timezone)
            for timezone in timezones if current.lower() in timezone.lower()
        ]

    @timestamp.autocomplete('date')
    async def timezones_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=datetime.utcnow().strftime('%d/%b/%Y'), value=datetime.utcnow().strftime('%d/%b/%Y'))]

    @timestamp.autocomplete('time')
    async def timezones_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=datetime.utcnow().strftime('%H:%M'), value=datetime.utcnow().strftime('%H:%M'))]
    
    @tasks.loop(minutes=1)
    async def update_time(self):
        # get current time in America/Los_Angeles
        current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
        time = current_time.strftime('%I:%M %p')
        # Check if it's a 10 minute interval
        if current_time.minute % 10 == 0:
            # set channel name to current time
            channel: CategoryChannel = self.client.get_channel(567147619122544641)
            await channel.edit(name=f'PEPPER TIME: {time}')


    @update_time.before_loop
    async def before_update_time(self):
        await self.client.wait_until_ready()


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Timestamp(self))
