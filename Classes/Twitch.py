import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from discord import Embed, Color
from discord.ext import commands
from twitchAPI.chat import Chat, EventData, ChatMessage
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import refresh_access_token
from twitchAPI.object.eventsub import ChannelUpdateEvent, StreamOnlineEvent, StreamOfflineEvent
from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent

from Classes.Database.User import User


class PlaceholderThread:
    def __init__(self, id):
        self.id = id


class TwitchBot:
    def __init__(self, discordBot: commands.Bot):
        self.discordBot = discordBot
        self.BOT_TARGET_SCOPES = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.MODERATION_READ]
        self.twitch_bot = None
        self.channel_user = None
        self.bot_user = None
        self.chat = None

    async def on_prediction_event(self, uuid: UUID, data: dict):
        # Extracting event type and prediction data
        event_type = data["type"]
        prediction = data["data"]
        embed = None
        embedMessage = None
        # Dict for color mapping
        color_emotes = {
            "BLUE": "🟦",
            "PINK": "🟪",
        }

        # Helper function to create an embed with a given title and color
        def create_embed(title, color=Color.green()):
            return Embed(title=title, color=color)

        # Helper function to format the ISO string
        def format_iso_str(iso_str):
            iso_str = iso_str.rstrip("Z")
            if "." in iso_str:
                date_str, time_str = iso_str.split("T")
                time_str, fractional = time_str.split(".")
                fractional = fractional[:6]  # Truncate to 6 digits
                return f"{date_str}T{time_str}.{fractional}"
            return iso_str

        # Handling event-created type
        if event_type == "event-created":
            embed = create_embed(f"Prediction Created: {prediction['event']['title']}")
            # Convert ISO string to datetime object
            created_at = datetime.fromisoformat(format_iso_str(prediction["event"]["created_at"])).replace(
                tzinfo=timezone.utc)
            # Calculate the lock timestamp
            lock_timestamp = int(
                (created_at + timedelta(seconds=prediction["event"]["prediction_window_seconds"])).timestamp())
            # Set the embed message
            embedMessage = '<@&1080237787174948936>'
            embed.description = f"Prediction will be locked <t:{lock_timestamp}:R>"
            embed.add_field(name="Outcomes", value="\n".join(
                [f"{color_emotes[outcome['color']]} {outcome['title']}" for outcome in
                 prediction["event"]["outcomes"]]),
                            inline=False)

        # Handling event-updated type
        elif event_type == "event-updated":
            predictionTitle = prediction["event"]["title"]
            # Calculate total points and users for the event
            total_points = sum(outcome["total_points"] for outcome in prediction["event"]["outcomes"])
            total_users = sum(outcome["total_users"] for outcome in prediction["event"]["outcomes"])

            # If the event status is LOCKED
            if prediction["event"]["status"] == "LOCKED":
                embed = create_embed(f"Prediction Locked: {predictionTitle}")
                for outcome in prediction["event"]["outcomes"]:
                    user_percentage = (outcome["total_users"] / total_users) * 100
                    points_percentage = (outcome["total_points"] / total_points) * 100
                    ratio = total_points / outcome["total_points"]
                    top_predictors_str = "\n".join(
                        [f"{predictor['user_display_name']} bet {predictor['points']} points" for predictor in
                         outcome["top_predictors"][:5]]) or "None"
                    embed.add_field(name=f"{color_emotes[outcome['color']]} Outcome: {outcome['title']}",
                                    value=f"Points: {outcome['total_points']} ({points_percentage:.2f}%)\nUsers: {outcome['total_users']} ({user_percentage:.2f}%)\nRatio: {ratio:.2f}\n**Top Predictors:**\n{top_predictors_str}",
                                    inline=False)

            # If the event status is RESOLVED
            elif prediction["event"]["status"] == "RESOLVED":
                embed = create_embed(f"Prediction Resolved: {predictionTitle}")
                winning_outcome_id = prediction["event"]["winning_outcome_id"]
                total_points = sum(outcome["total_points"] for outcome in prediction["event"]["outcomes"])
                total_users = sum(outcome["total_users"] for outcome in prediction["event"]["outcomes"])

                for outcome in prediction["event"]["outcomes"]:
                    is_winner = "✅" if outcome["id"] == winning_outcome_id else "❌"
                    user_percentage = (outcome["total_users"] / total_users) * 100
                    points_percentage = (outcome["total_points"] / total_points) * 100
                    ratio = total_points / outcome["total_points"]
                    top_predictors_str = "\n".join([
                        f"{predictor['user_display_name']} {'won' if predictor['result']['type'] == 'WIN' else 'lost'} {predictor['result']['points_won'] if predictor['result']['points_won'] is not None else predictor['points']} points"
                        for predictor in outcome["top_predictors"][:5]]) or "None"
                    embed.add_field(name=f"{color_emotes[outcome['color']]} Outcome: {outcome['title']} {is_winner}",
                                    value=f"Points: {outcome['total_points']} ({points_percentage:.2f}%)\nUsers: {outcome['total_users']} ({user_percentage:.2f}%)\nRatio: {ratio:.2f}\n**Top Predictors:**\n{top_predictors_str}",
                                    inline=False)

        # If an embed was created, send it via webhook
        if embed:
            await self.discordBot.settings.twitch_gambling_channel.send(embedMessage, embed=embed)

    async def on_channel_update(self, data: ChannelUpdateEvent):
        # Create and embed of the channel update
        embed = Embed(title=f"Channel Update: {data.event.broadcaster_user_name}", color=Color.green())
        embed.add_field(name="Title", value=data.event.title, inline=True)
        embed.add_field(name="Category", value=data.event.category_name, inline=True)
        # Send the embed to the mod channel
        await self.discordBot.settings.twitch_mod_channel.send(embed=embed)

    async def on_stream_online(self, data: StreamOnlineEvent):
        # Create and embed of the channel update
        embed = Embed(title=f"Stream Online: {data.event.broadcaster_user_name}", color=Color.green())
        # Send the embed to the mod channel
        await self.discordBot.settings.twitch_mod_channel.send(embed=embed)

    async def on_stream_offline(self, data: StreamOfflineEvent):
        # Create and embed of the channel update
        embed = Embed(title=f"Stream Offline: {data.event.broadcaster_user_name}", color=Color.red())
        # Send the embed to the mod channel
        await self.discordBot.settings.twitch_mod_channel.send(embed=embed)

    async def on_chat_ready(self, data: EventData):
        logging.getLogger("Twitch").info('Chat is ready for work, joining channels')
        await data.chat.join_room(self.twitch_channel_name)

    async def on_chat_joined(self, data: EventData):
        logging.getLogger("Twitch").info(f"User {data.user_name} joined the chat {data.room_name}")

    async def on_chat_message(self, msg: ChatMessage):
        if msg.text == "wah, you up?" and msg.user.mod:
            await msg.reply("Let me sleep")
        if msg.text.startswith('DMC-'):
            try:
                query = f"SELECT * FROM u WHERE u.mc_redeem = '{msg.text}'"
                dbUserResult = await User(self.discordBot.database).query_users(query)
                # Get the first result
                dbUser: dict = [item async for item in dbUserResult][0]
                dbUserID = dbUser['id']
                if dbUser:
                    # Post embed for redemption
                    embed = Embed(title=f"Minecraft Redemption: {msg.user.display_name}", color=Color.orange())
                    embed.set_footer(
                        text="Please ensure the user has redeemed on twitch and approve in the redemption queue once complete")
                    embed.add_field(name="Twitch Username", value=msg.user.display_name, inline=True)
                    embed.add_field(name="Discord ID", value=dbUserID, inline=True)
                    embed.add_field(name="Discord Mention", value=f"<@{dbUserID}>", inline=True)
                    # Send the embed to the mod channel
                    await self.discordBot.settings.twitch_mod_channel.send(embed=embed)
                    # respond to the user
                    await msg.reply(f"Successfully redeemed, please wait for a mod to check your info")
                    # Remove the code from the database
                    dbUser.pop('mc_redeem')
                    await User(self.discordBot.database).update_user(dbUserID, dbUser)
                else:
                    raise Exception("Invalid code")
            except Exception as e:
                logging.getLogger("Twitch").exception(f"Error redeeming code: {e}")
                await msg.reply(f"Invalid code, please contact the mods in #staff-support on discord")

    async def run(self):
        self.twitch_client_id = self.discordBot.settings.twitch_client_id
        self.twitch_client_secret = self.discordBot.settings.twitch_client_secret
        self.twitch_bot_name = self.discordBot.settings.twitch_bot_name
        self.twitch_bot_refresh_token = self.discordBot.settings.twitch_bot_refresh_token
        self.twitch_channel_name = self.discordBot.settings.twitch_channel_name
        # Set up the Twitch instance for the bot
        self.twitch_bot = await Twitch(self.twitch_client_id,
                                       self.twitch_client_secret)
        self.bot_user = await first(self.twitch_bot.get_users(logins=[self.twitch_bot_name]))
        self.channel_user = await first(
            self.twitch_bot.get_users(logins=self.twitch_channel_name))
        bot_tokens = await refresh_access_token(self.twitch_bot_refresh_token,
                                                self.twitch_client_id,
                                                self.twitch_client_secret)
        await self.twitch_bot.set_user_authentication(bot_tokens[0], self.BOT_TARGET_SCOPES,
                                                      refresh_token=bot_tokens[1])
        logging.getLogger("Twitch").info(f'Twitch Bot ID: {self.bot_user.id}')
        # Set up the pubsub
        pubsub = PubSub(self.twitch_bot, self.discordBot.loop)
        pubsub.start()
        await pubsub.listen_undocumented_topic(f"predictions-channel-v1.{self.channel_user.id}",
                                               self.on_prediction_event)
        logging.getLogger("Twitch").info('Twitch PubSub listening')
        # Set up EventSub
        eventsub = EventSubWebsocket(self.twitch_bot, callback_loop=self.discordBot.loop)
        eventsub.start()
        await eventsub.listen_channel_update_v2(self.channel_user.id, self.on_channel_update)
        await eventsub.listen_stream_online(self.channel_user.id, self.on_stream_online)
        await eventsub.listen_stream_offline(self.channel_user.id, self.on_stream_offline)
        logging.getLogger("Twitch").info('Twitch EventSub listening')
        # Set up the chat
        self.chat = await Chat(self.twitch_bot, callback_loop=self.discordBot.loop)
        self.chat.set_prefix("✵")
        self.chat.register_event(ChatEvent.READY, self.on_chat_ready)
        self.chat.register_event(ChatEvent.JOINED, self.on_chat_joined)
        self.chat.register_event(ChatEvent.MESSAGE, self.on_chat_message)
        self.chat.register_event(ChatEvent.LEFT, self.on_chat_ready)
        self.chat.start()
        logging.getLogger("Twitch").info('Twitch Chat listening')
