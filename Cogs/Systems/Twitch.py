from datetime import datetime

from discord import Embed, Color
from twitchAPI import Twitch
from twitchAPI.chat import Chat, EventData, ChatMessage
from twitchAPI.eventsub import EventSub
from twitchAPI.helper import first
from twitchAPI.oauth import refresh_access_token
from twitchAPI.types import AuthScope, ChatEvent
from discord.ext import commands


class TwitchBot(commands.Cog):
    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.BOT_TARGET_SCOPES = [AuthScope.WHISPERS_EDIT, AuthScope.WHISPERS_READ, AuthScope.USER_MANAGE_WHISPERS,
                                  AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
        self.twitch_bot = None
        self.channel_user = None
        self.bot_user = None
        self.chat = None

    async def on_minecraft_redemption(self, data: dict):
        user_id = data['event']['user_id']
        message = "Thanks for redeeming Minecraft access, Please join the discord and complete this form https://forms.gle/oouvNweqqBFZ8DtD9"
        # await self.chat.send_message(self.channel_user.display_name, message)
        # await self.twitch_bot.send_whisper(self.bot_user.id, user_id, message)
        print(data)

    async def on_prediction_begin(self, data: dict):
        # Extract prediction data
        prediction = data['event']
        title = prediction['title']
        outcomes = prediction['outcomes']
        started_at = datetime.fromisoformat(prediction['started_at'])
        locks_at = datetime.fromisoformat(prediction['locks_at'])
        prediction_time = prediction['prediction_window']

        # Create base embed
        embed = Embed(title=f"Prediction Created: {title}", timestamp=started_at, color=Color.green())
        embed.description = f"Voting ends: {locks_at.strftime('%Y-%m-%d %H:%M:%S')}"
        embed.add_field(name="Outcomes", value="\n".join([o['title'] for o in outcomes]))
        message_content = "<@&1080237787174948936>"

        # Send message
        # For now, just printing the embed title and description
        print(embed.title)
        print(embed.description)

    async def on_prediction_lock(self, data: dict):
        # Extract prediction data
        prediction = data['event']
        title = prediction['title']
        outcomes = prediction['outcomes']

        # Create base embed
        embed = Embed(title=f"Prediction Locked: {title}", color=Color.blue())
        embed.description = "The prediction is now locked and no further votes can be cast."

        # Add outcomes to the embed
        for outcome in outcomes:
            # Calculate the ratio
            total_points = sum([predictor['channel_points_used'] for predictor in outcome['top_predictors']])
            ratio = outcome.get('channel_points', 0) / total_points if total_points > 0 else 0

            # Get top 5 predictors
            top_predictors = "\n".join(
                [f"{predictor['user_name']} ({predictor['channel_points_used']} points)" for predictor in
                 outcome['top_predictors'][:5]])

            # Add outcome details to the embed
            outcome_details = (
                f"Users: {outcome.get('users', 0)}\n"
                f"Points: {outcome.get('channel_points', 0)}\n"
                f"Ratio: {ratio:.2f}\n"
                f"Top 5 Predictors:\n{top_predictors}"
            )
            embed.add_field(name=outcome['title'], value=outcome_details, inline=False)

        # Send message
        # For now, just printing the embed title, description, and fields
        print(embed.title)
        print(embed.description)
        for field in embed.fields:
            print(f"{field.name}\n{field.value}\n{'-' * 40}")

    async def on_prediction_end(self, data: dict):
        # Extract prediction data
        prediction = data['event']
        title = prediction['title']
        outcomes = prediction['outcomes']
        winning_outcome_id = prediction['winning_outcome_id']
        status = prediction['status']

        # Create base embed
        embed_color = Color.green() if status == "resolved" else Color.red()
        embed = Embed(title=f"Prediction Ended: {title}", color=embed_color)
        embed.description = f"The prediction has {status}."

        # Add outcomes to the embed
        for outcome in outcomes:
            # Determine if this outcome was the winning one
            is_winner = outcome['id'] == winning_outcome_id

            # Get top 5 predictors and their earnings/losses
            top_predictors = "\n".join(
                [
                    f"{predictor['user_name']} ({'+ ' if predictor['channel_points_won'] else '- '}{predictor['channel_points_used']} points)"
                    for predictor in outcome['top_predictors'][:5]
                ]
            )

            # Add outcome details to the embed
            outcome_title = f"{'🏆 ' if is_winner else ''}{outcome['title']}"
            outcome_details = (
                f"Users: {outcome.get('users', 0)}\n"
                f"Points: {outcome.get('channel_points', 0)}\n"
                f"Top 5 Predictors:\n{top_predictors}"
            )
            embed.add_field(name=outcome_title, value=outcome_details, inline=False)

        # Send message
        # For now, just printing the embed title, description, and fields
        print(embed.title)
        print(embed.description)
        for field in embed.fields:
            print(f"{field.name}\n{field.value}\n{'-' * 40}")

    async def on_chat_ready(self, data: EventData):
        print('Chat ready')

    async def on_chat_joined(self, data: EventData):
        print(f"User {data.user_name} joined the chat {data.room_name}")

    async def on_chat_message(msg: ChatMessage):
        print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')

    async def run_twitch_bot(self):
        # Set up the Twitch instance for the bot
        self.twitch_bot = await Twitch(self.discord_client.settings.twitch_client_id,
                                       self.discord_client.settings.twitch_client_secret)
        self.bot_user = await first(self.twitch_bot.get_users(logins=[self.discord_client.settings.twitch_bot_name]))
        self.channel_user = await first(
            self.twitch_bot.get_users(logins=self.discord_client.settings.twitch_channel_name))
        bot_tokens = await refresh_access_token(self.discord_client.settings.twitch_bot_refresh_token,
                                                self.discord_client.settings.twitch_client_id,
                                                self.discord_client.settings.twitch_client_secret)
        await self.twitch_bot.set_user_authentication(bot_tokens[0], self.BOT_TARGET_SCOPES,
                                                      refresh_token=bot_tokens[1])
        print(f'Twitch Bot ID: {self.bot_user.id}')
        # Set up the eventsub
        event_sub = EventSub(self.discord_client.settings.twitch_eventsub_url,
                             self.discord_client.settings.twitch_client_id, 8080, self.twitch_bot)
        await event_sub.unsubscribe_all()
        event_sub.start()
        await event_sub.listen_channel_points_custom_reward_redemption_add(self.channel_user.id,
                                                                           self.on_minecraft_redemption,
                                                                           'a5b9d1c7-44f9-4964-b0f7-42c39cb04f98')
        # await event_sub.listen_channel_prediction_begin(self.channel_user.id, self.on_prediction_begin)
        # await event_sub.listen_channel_prediction_lock(self.channel_user.id, self.on_prediction_lock)
        # await event_sub.listen_channel_prediction_end(self.channel_user.id, self.on_prediction_end)
        print('EventSub listening')
        # Set up the chat
        self.chat = Chat(self.twitch_bot, initial_channel=[self.channel_user.display_name])
        self.chat.register_event(ChatEvent.READY, self.on_chat_ready)
        self.chat.register_event(ChatEvent.JOINED, self.on_chat_joined)
        self.chat.register_event(ChatEvent.MESSAGE, self.on_chat_message)
        # self.chat.start()
        print('Chat listening')

    @commands.Cog.listener()
    async def on_ready(self):
        await self.run_twitch_bot()

async def setup(bot):
    await bot.add_cog(TwitchBot(bot))
