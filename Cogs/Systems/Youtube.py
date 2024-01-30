import logging
import traceback

import discord
import isodate
from discord.ext import commands, tasks
from pyyoutube import Api


class CheckYoutube(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.api: Api = Api(api_key=self.client.settings['youtube_api'])
        self.monitor.start()  # Start the background task

    @tasks.loop(minutes=5)
    async def monitor(self):
        response = ""
        # Make sure the settings are loaded
        await self.client.load_settings()
        for youtube_config in self.client.settings['youtube_settings']:
            try:
                uploads_playlist_id = youtube_config.get('upload_playlist_id')
                if not uploads_playlist_id:
                    channel_info = self.api.get_channel_info(channel_id=youtube_config["youtube_id"])
                    uploads_playlist_id = channel_info.items[0].contentDetails.relatedPlaylists.uploads
                    youtube_config['upload_playlist_id'] = uploads_playlist_id

                videos = self.api.get_playlist_items(playlist_id=youtube_config['upload_playlist_id'], count=1)
                video_id = videos.items[0].snippet.resourceId.videoId

                last_video_id = youtube_config['last_video_id']
                if video_id == last_video_id or last_video_id is None:
                    continue

                response += f"\n{youtube_config['youtube_id']}\n- database: {last_video_id}\n- youtube: {video_id}"

                video_details = self.api.get_video_by_id(video_id=video_id).items[0]
                channel_name = video_details.snippet.channelTitle
                channel_url = f"https://www.youtube.com/channel/{youtube_config['youtube_id']}"
                video_title = video_details.snippet.title
                video_thumbnail = video_details.snippet.thumbnails.high.url
                video_id = video_details.id
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                duration = video_details.contentDetails.duration
                duration = isodate.parse_duration(duration).total_seconds()

                # Ignore streams
                is_live = video_details.snippet.liveBroadcastContent
                if is_live == 'upcoming' or is_live == 'live':
                    response += f"\n- Skipping Live"
                    continue

                # Create the embed
                embed = discord.Embed(title=video_title, url=video_url)
                embed.set_author(name=channel_name, url=channel_url)
                embed.set_image(url=video_thumbnail)

                post_channel = self.client.get_channel(int(youtube_config['post_channel_id']))
                mention_role = f'<@&{youtube_config["mention_role_id"]}>'

                # Dont ping shorts
                if duration < 60:
                    mention_role = ''
                    response += f"\n- Skipping Short"

                ## If is the vod channel and title does not contain VOD
                if youtube_config['youtube_id'] == 'UCzL0SBEypNk4slpzSbxo01g' and video_title.find('(VOD)') == -1:
                    mention_role = f'<@&812501073289805884>'

                await post_channel.send(f"{mention_role}", embed=embed)
                response += f"\n- Posted"

                # Update the last video ID
                youtube_config['last_video_id'] = video_id
            except Exception as e:
                logging.getLogger("YoutubeChannel").error(f"{youtube_config['id']}\n\n{e}\n{traceback.format_exc()}")

        collection = self.client.database.BotSettings
        await collection.update_one({'_id': self.client.settings['_id']},
                                    {'$set': {'youtube_settings': self.client.settings['youtube_settings']}})
        await self.client.load_settings()
        if response != "":
            logging.getLogger('YoutubeChannel').info(response)

    @monitor.before_loop
    async def before_monitor(self):
        await self.client.wait_until_ready()


async def setup(client):
    await client.add_cog(CheckYoutube(client))
