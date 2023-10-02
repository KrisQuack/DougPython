import logging
import xml.etree.ElementTree as ET
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands, tasks


class CheckYoutube(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.session = aiohttp.ClientSession()
        self.monitor.start()  # Start the background task

    @tasks.loop(minutes=10)
    async def monitor(self):
        # Make sure the settings are loaded
        await self.client.settings.get_settings(self.client)
        for youtube_config in self.client.settings.dict['youtube_settings']:
            try:
                async with self.session.get(
                        f'https://www.youtube.com/feeds/videos.xml?channel_id={youtube_config["youtube_id"]}') as r:
                    if r.status == 200:
                        text = await r.text()
                        root = ET.fromstring(text)

                        # Parse XML to get channel and video details
                        channel = root.find(".//{http://www.w3.org/2005/Atom}author")
                        channel_name = channel.find("{http://www.w3.org/2005/Atom}name").text
                        channel_url = channel.find("{http://www.w3.org/2005/Atom}uri").text

                        latest_video = sorted(
                            root.findall(".//{http://www.w3.org/2005/Atom}entry"),
                            key=lambda e: datetime.fromisoformat(e.find("{http://www.w3.org/2005/Atom}published").text),
                            reverse=True
                        )[0]

                        video_title = latest_video.find("{http://www.w3.org/2005/Atom}title").text
                        video_thumbnail = latest_video.find(".//{http://search.yahoo.com/mrss/}thumbnail").attrib['url']
                        video_id = latest_video.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
                        video_url = latest_video.find("{http://www.w3.org/2005/Atom}link").attrib['href']

                        last_video_id = youtube_config['last_video_id']
                        if video_id == last_video_id or last_video_id is None:
                            continue

                        # Create the embed
                        embed = discord.Embed(title=video_title, url=video_url)
                        embed.set_author(name=channel_name, url=channel_url)
                        embed.set_image(url=video_thumbnail)

                        post_channel = self.client.get_channel(int(youtube_config['post_channel_id']))
                        mention_role = f'<@&{youtube_config["mention_role_id"]}>'

                        ## If is the vod channel and title does not contain VOD
                        if youtube_config['youtube_id'] == 'UCzL0SBEypNk4slpzSbxo01g' and video_title.find('VOD') == -1:
                            mention_role = f'<@&812501073289805884>'

                        await post_channel.send(f"{mention_role}", embed=embed)

                        # Update the last video ID
                        youtube_config['last_video_id'] = video_id
            except Exception as e:
                logging.getLogger("YoutubeChannel").error(f"{youtube_config['id']}\n\n{e}")

        await self.client.settings.update_settings()

    @monitor.before_loop
    async def before_monitor(self):
        await self.client.wait_until_ready()


async def setup(client):
    await client.add_cog(CheckYoutube(client))
