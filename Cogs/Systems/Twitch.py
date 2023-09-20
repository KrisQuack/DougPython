from datetime import datetime, timedelta, timezone
import logging

from discord import Embed, Color
from discord.ext import commands
from discord import SyncWebhook
from twitchAPI import Twitch
from twitchAPI.chat import Chat, EventData, ChatMessage
from twitchAPI.helper import first
from twitchAPI.oauth import refresh_access_token
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.pubsub import PubSub
from uuid import UUID

class PlaceholderThread:
    def __init__(self, id):
        self.id = id


class TwitchBot(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.BOT_TARGET_SCOPES = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.MODERATION_READ]
        self.twitch_bot = None
        self.channel_user = None
        self.bot_user = None
        self.chat = None

    async def initialize_async(self):
        settingDict = self.client.settings.settingDict
        self.twitch_client_id = settingDict["twitch_client_id"]
        self.twitch_client_secret = settingDict["twitch_client_secret"]
        self.twitch_bot_name = settingDict["twitch_bot_name"]
        self.twitch_bot_refresh_token = settingDict["twitch_bot_refresh_token"]
        self.twitch_channel_name = settingDict["twitch_channel_name"]
        return self

    async def on_prediction_event(self, uuid: UUID, data: dict):
        # Extracting event type and prediction data
        event_type = data["type"]
        prediction = data["data"]
        embed = None
        embedMessage = None

        # Helper function to create an embed with a given title and color
        def create_embed(title, color=Color.green()):
            return Embed(title=title, color=color)

        # Helper function to send the webhook message
        def send_webhook(embed, message):
            ##### ADD TO DATABASE #####
            webhook = SyncWebhook.from_url('https://discord.com/api/webhooks/1153761373923315783/PmpyjoH58xx9N2SvpH6BYrxqVh1844FhJcFahUaqlGGq15RY35HfyI8iHWpu-SPPWdKc')
            thread = PlaceholderThread(1070317311505997864)
            webhook.send(message, embed=embed, thread=thread)

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
            created_at = datetime.fromisoformat(format_iso_str(prediction["event"]["created_at"])).replace(tzinfo=timezone.utc)
            # Calculate the lock timestamp
            lock_timestamp = int((created_at + timedelta(seconds=prediction["event"]["prediction_window_seconds"])).timestamp())
            embedMessage = '<@&1080237787174948936>'
            embed.description = f"Prediction will be locked <t:{lock_timestamp}:R>"
            embed.add_field(name="Outcomes", value="\n".join([f"{outcome['title']}: {outcome['color']}" for outcome in prediction["event"]["outcomes"]]), inline=False)

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
                    top_predictors_str = "\n".join([f"{predictor['user_display_name']} bet {predictor['points']} points" for predictor in outcome["top_predictors"][:5]]) or "None"
                    embed.add_field(name=f"Outcome: {outcome['title']} ({outcome['color']})", 
                                value=f"Points: {outcome['total_points']} ({points_percentage:.2f}%)\nUsers: {outcome['total_users']} ({user_percentage:.2f}%)\nRatio: {ratio:.2f}\n**Top Predictors:**\n{top_predictors_str}", 
                                inline=False)

            # If the event status is RESOLVED
            elif prediction["event"]["status"] == "RESOLVED":
                embed = create_embed(f"Prediction Resolved: {predictionTitle}")
                winning_outcome_id = prediction["event"]["winning_outcome_id"]

                for outcome in prediction["event"]["outcomes"]:
                    is_winner = "✅" if outcome["id"] == winning_outcome_id else "❌"
                    ratio = total_points / outcome["total_points"]
                    result_text = "\n".join([f"{predictor['user_display_name']} {'won' if predictor['result']['type'] == 'WIN' else 'lost'} {predictor['result'].get('points_won', predictor['points'])} points" for predictor in outcome["top_predictors"][:5]]) or "None"
                    embed.add_field(name=f"Outcome: {outcome['title']} ({outcome['color']}) {is_winner}", 
                                value=f"Points: {outcome['total_points']} ({points_percentage:.2f}%)\nUsers: {outcome['total_users']} ({user_percentage:.2f}%)\nRatio: {ratio:.2f}\n**Top Predictors:**\n{result_text}", 
                                inline=False)

        # If an embed was created, send it via webhook
        if embed:
            send_webhook(embed, embedMessage)



    async def on_chat_ready(self, data: EventData):
        logging.info('Chat is ready for work, joining channels')
        await data.chat.join_room(self.twitch_channel_name)

    async def on_chat_joined(self, data: EventData): 
        logging.info(f"User {data.user_name} joined the chat {data.room_name}")

    async def on_chat_message(self, msg: ChatMessage):
        if msg.text == "wah, you up?" and msg.user.mod:
            await msg.reply("Let me sleep")
        ##### I will need to process Minecrat requests here #####

    async def run_twitch_bot(self):
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
        logging.info(f'Twitch Bot ID: {self.bot_user.id}')
        # Set up the pubsub
        pubsub = PubSub(self.twitch_bot)
        pubsub.start()
        # you can either start listening before or after you started pubsub.
        await pubsub.listen_undocumented_topic(f"predictions-channel-v1.{self.channel_user.id}", self.on_prediction_event)
        # Set up the chat
        self.chat = await Chat(self.twitch_bot)
        self.chat.register_event(ChatEvent.READY, self.on_chat_ready)
        self.chat.register_event(ChatEvent.JOINED, self.on_chat_joined)
        self.chat.register_event(ChatEvent.MESSAGE, self.on_chat_message)
        self.chat.start()
        logging.info('Twitch Chat listening')


async def setup(bot):
    bot_cog = await TwitchBot(bot).initialize_async()
    bot.loop.create_task(bot_cog.run_twitch_bot())
    await bot.add_cog(bot_cog)
