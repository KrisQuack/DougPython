import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import pytz

class Timestamp(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="timestamp", description="Convert a date and time to a Discord timestamp")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timestamp(self, interaction: discord.Interaction, date_string: str):
        # Extract the time zone from the date_string
        time_zone_pos = date_string.rfind(' ')
        tz_str = date_string[time_zone_pos + 1:]

        # Check if the time zone is valid
        if tz_str not in pytz.all_timezones:
            await interaction.response.send_message("Invalid time zone.", ephemeral=True)
            print(pytz.all_timezones)
            return

        # Remove the time zone from the date_string
        date_string = date_string[:time_zone_pos]

        # Convert to datetime object and then to Unix timestamp
        try:
            parsed_time = datetime.strptime(date_string, '%d %b %Y %H:%M')
        except ValueError:
            try:
                parsed_time = datetime.strptime(date_string, '%H:%M')
            except ValueError:
                await interaction.response.send_message("Invalid time format. Please use `12:00 GMT` or `01 Jan 2022 12:00 GMT`.", ephemeral=True)
                return

        # Apply the time zone
        tz = pytz.timezone(tz_str)
        parsed_time = tz.localize(parsed_time)

        parsed_unix_time = int(parsed_time.timestamp())

        # Create Discord embed
        embed = discord.Embed(title="Time Stamp", color=discord.Color.blue())
        embed.add_field(name="Relative Time", value=f"`<t:{parsed_unix_time}:R>` : <t:{parsed_unix_time}:R>", inline=False)
        embed.add_field(name="Absolute Time", value=f"`<t:{parsed_unix_time}:F>` : <t:{parsed_unix_time}:F>", inline=False)
        embed.add_field(name="Short Date", value=f"`<t:{parsed_unix_time}:f>` : <t:{parsed_unix_time}:f>", inline=False)
        embed.add_field(name="Long Time", value=f"`<t:{parsed_unix_time}:T>` : <t:{parsed_unix_time}:T>", inline=False)
        embed.add_field(name="Short Time", value=f"`<t:{parsed_unix_time}:t>` : <t:{parsed_unix_time}:t>", inline=False)

        await interaction.response.send_message(content=f"<t:{parsed_unix_time}:t> <t:{parsed_unix_time}:R>", embed=embed, ephemeral=True)

async def setup(self: commands.Bot) -> None:
    await self.add_cog(Timestamp(self))
