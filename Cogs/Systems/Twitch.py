from datetime import datetime, timedelta

from discord import Embed, Color
from discord.ext import commands
from discord import Webhook
from twitchAPI import Twitch
from twitchAPI.chat import Chat, EventData, ChatMessage
from twitchAPI.helper import first
from twitchAPI.oauth import refresh_access_token
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.pubsub import PubSub
from uuid import UUID
import aiohttp

from Database.BotSettings import BotSettings


class TwitchBot(commands.Cog):
    def __init__(self):
        self.BOT_TARGET_SCOPES = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.MODERATION_READ]
        self.twitch_bot = None
        self.channel_user = None
        self.bot_user = None
        self.chat = None

    async def initialize_async(self):
        self.twitch_client_id = await BotSettings.get_twitch_client_id()
        self.twitch_client_secret = await BotSettings.get_twitch_client_secret()
        self.twitch_bot_name = await BotSettings.get_twitch_bot_name()
        self.twitch_bot_refresh_token = await BotSettings.get_twitch_bot_refresh_token()
        self.twitch_channel_name = await BotSettings.get_twitch_channel_name()
        return self

    async def on_prediction_event(self, uuid: UUID, data: dict):
        event_type = data["type"]
        prediction = data["data"]
        embed = None
        if event_type == "event-created":
            predictionTitle = prediction["event"]["title"]
            embed = Embed(title=f"Prediction Created: {predictionTitle}", color=Color.green())
            
            # Calculate the UNIX timestamp for when the prediction will be locked
            created_at = datetime.fromisoformat(prediction["event"]["created_at"].rstrip("Z"))
            lock_time = created_at + timedelta(seconds=prediction["event"]["prediction_window_seconds"])
            lock_timestamp = int(lock_time.timestamp())
            
            embed.description = f"Prediction will be locked <t:{lock_timestamp}:R>"
            embed.add_field(name="Outcomes", value="\n".join([f"{outcome['title']}: {outcome['color']}" for outcome in prediction["event"]["outcomes"]]), inline=False)
            
        if event_type == "event-updated" and prediction["event"]["status"] == "LOCKED":
            predictionTitle = prediction["event"]["title"]
            embed = Embed(title=f"Prediction Locked: {predictionTitle}", color=Color.green())
            
            for outcome in prediction["event"]["outcomes"]:
                outcome_title = outcome["title"]
                outcome_color = outcome["color"]
                
                top_predictors_text = []
                for predictor in outcome["top_predictors"]:
                    points_bet = predictor["points"]
                    user_display_name = predictor["user_display_name"]
                    top_predictors_text.append(f"{user_display_name} bet {points_bet} points")
                
                top_predictors_str = "\n".join(top_predictors_text) or "None"
                
                embed.add_field(name=f"Outcome: {outcome_title} ({outcome_color})", 
                                value=f"Top Predictors:\n{top_predictors_str}", 
                                inline=False)
        if event_type == "event-updated" and prediction["event"]["status"] == "RESOLVED":
            predictionTitle = prediction["event"]["title"]
            embed = Embed(title=f"Prediction Resolved: {predictionTitle}", color=Color.green())
            
            winning_outcome_id = prediction["event"]["winning_outcome_id"]
            
            for outcome in prediction["event"]["outcomes"]:
                outcome_title = outcome["title"]
                outcome_color = outcome["color"]
                total_points = outcome["total_points"]
                total_users = outcome["total_users"]
                ratio = 0 if total_users == 0 else total_points / total_users
                
                # Determine if this outcome was the winning one
                is_winner = "✅" if outcome["id"] == winning_outcome_id else "❌"
                
                top_predictors_text = []
                for predictor in outcome["top_predictors"]:
                    result_type = predictor["result"]["type"]
                    points_won = predictor["result"]["points_won"]
                    user_display_name = predictor["user_display_name"]
                    result_text = f"won {points_won} points" if result_type == "WIN" else f"lost {points_won} points"
                    top_predictors_text.append(f"{user_display_name} {result_text}")
                
                top_predictors_str = "\n".join(top_predictors_text) or "None"
                
                embed.add_field(name=f"Outcome: {outcome_title} ({outcome_color}) {is_winner}", 
                                value=f"Points: {total_points}\nUsers: {total_users}\nRatio: {ratio:.2f}\nTop Predictors:\n{top_predictors_str}", 
                                inline=False)
        
        if embed:
            ##### set these in the database #####
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url('https://discord.com/api/webhooks/1151245523404193802/X1pFAQTYO7mf4V5O6rCorUUiAjO5DrBptoIyKpvmJaLR7VOaI8TGWtWNM-JGS1JBKUA3', session=session)
                await webhook.send('<@&1080237787174948936>', embed=embed)


    async def on_chat_ready(self, data: EventData):
        print('Chat is ready for work, joining channels')
        await data.chat.join_room(self.twitch_channel_name)

    async def on_chat_joined(self, data: EventData): 
        print(f"User {data.user_name} joined the chat {data.room_name}")

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
        print(f'Twitch Bot ID: {self.bot_user.id}')
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
        print('Chat listening')


async def setup(bot):
    bot_cog = await TwitchBot().initialize_async()
    bot.loop.create_task(bot_cog.run_twitch_bot())
    await bot.add_cog(bot_cog)
