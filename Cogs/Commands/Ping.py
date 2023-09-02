import time

import discord
from discord import app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        # WebSocket latency
        ws_latency = round(self.client.latency * 1000)

        # Measure HTTP latency by timing how long it takes to send a message
        start_time = time.time()
        msg = await interaction.channel.send("Calculating HTTP latency...")
        end_time = time.time()
        await msg.delete()

        http_latency = round((end_time - start_time) * 1000)  # Convert to milliseconds

        # Create an embed to display the latencies
        embed = discord.Embed(
            title="Pong!",
            description=f"WebSocket Latency: {ws_latency}ms\nHTTP API Latency: {http_latency}ms",
            color=discord.Color.green()
        )

        # Send the embed
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Ping(self))
