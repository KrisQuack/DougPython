from datetime import datetime, timedelta

from discord import Member, Embed, Colour


async def Timeout_User(member: Member, duration: timedelta, reason: str):
    # Get the timeout expiration time as unix time
    expiration_datetime = datetime.utcnow() + duration  # Current UTC time + duration
    timestamp = int(expiration_datetime.timestamp())  # Convert to Unix timestamp
    # Timeout the user
    await member.timeout(duration, reason=reason)
    # Send the user a DM
    embed = Embed(title=f"Timeout",
                  description=f"Your timeout will be lifted <t:{timestamp}:R>",
                  color=Colour.orange())
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Duration", value=f"{duration}", inline=False)
    embed.add_field(name="Expires", value=f"<t:{timestamp}:F>", inline=False)
    embed.set_footer(text=f"If you do not agree with this action, please respond here to get mods attention")
    await member.send(embed=embed)


async def Remove_Timeout_User(member: Member, reason: str):
    embed = Embed(title=f"UnTimeout",
                  description=f"You have been untimed out for {reason}",
                  color=Colour.green())
    await member.send(embed=embed)
    # Remove the timeout
    await member.timeout(reason=reason)


async def Ban_User(member: Member, reason: str, duration: timedelta):
    # Get the timeout expiration time as unix time
    expiration_datetime = datetime.utcnow() + duration  # Current UTC time + duration
    timestamp = expiration_datetime.timestamp()  # Convert to Unix timestamp
    embed = Embed(title=f"Ban",
                  description=f"You have been banned for <t:{timestamp}:R> for {reason}, this will expire on <t:{timestamp}:F>"
                              f"\n",
                  color=Colour.orange())
    embed.set_footer(text=f"If you do not agree with this action, please respond here to get mods attention")
    await member.send(embed=embed)
    # Ban the user
    await member.ban(reason=reason, delete_message_days=0)
