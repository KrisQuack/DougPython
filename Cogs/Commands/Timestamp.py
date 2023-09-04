from datetime import datetime
from typing import List

import discord
import pytz
from discord import app_commands
from discord.ext import commands


class Timestamp(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.date = '04/Jul/2000'

    @app_commands.command(name="timestamp", description="Convert a date and time to a Discord timestamp")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        date="The date to convert to a timestamp. Format: `04/Jul/2000`",
        time="The time to convert to a timestamp. Format: `18:00`",
        timezone="The time zone to use. Format: `America/Los_Angeles"
    )
    async def timestamp(self, interaction: discord.Interaction, date: str, time: str, timezone: str):
        # Check if the time zone is valid
        if timezone not in pytz.all_timezones:
            await interaction.response.send_message("Invalid time zone.", ephemeral=True)
            print(pytz.all_timezones)
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
        embed.add_field(name="Relative Time", value=f"`<t:{parsed_unix_time}:R>` : <t:{parsed_unix_time}:R>", inline=False)
        embed.add_field(name="Absolute Time", value=f"`<t:{parsed_unix_time}:F>` : <t:{parsed_unix_time}:F>", inline=False)
        embed.add_field(name="Short Date", value=f"`<t:{parsed_unix_time}:f>` : <t:{parsed_unix_time}:f>", inline=False)
        embed.add_field(name="Long Time", value=f"`<t:{parsed_unix_time}:T>` : <t:{parsed_unix_time}:T>", inline=False)
        embed.add_field(name="Short Time", value=f"`<t:{parsed_unix_time}:t>` : <t:{parsed_unix_time}:t>", inline=False)

        await interaction.response.send_message(content=f"<t:{parsed_unix_time}:t> <t:{parsed_unix_time}:R>", embed=embed, ephemeral=True)

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
            app_commands.Choice(name=datetime.now().strftime('%d/%b/%Y'), value=datetime.now().strftime('%d/%b/%Y'))]

    @timestamp.autocomplete('time')
    async def timezones_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        return [app_commands.Choice(name=datetime.now().strftime('%H:%M'), value=datetime.now().strftime('%H:%M'))]


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Timestamp(self))
