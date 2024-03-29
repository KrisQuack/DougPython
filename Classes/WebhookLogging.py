import asyncio
import logging
from logging import StreamHandler
from datetime import datetime
import os

from discord import Embed, Color


class WebhookLogging(logging.Handler):
    def __init__(self, client) -> None:
        self.client = client
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()
        self.stream_handler.setFormatter(self.formatter)
        self.error_timestamps = []

        # Initialize the log buffer
        self.embed_buffer = []

    async def run_polling(self):
        asyncio.create_task(self.log_sender())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name == "httpx":
                return

            self.stream_handler.emit(record)

            formatted_message = record.getMessage()
            formatted_message = formatted_message.replace('<', '&lt;').replace('>', '&gt;')
            color = Color.blue() if record.levelno == logging.INFO else Color.red() if record.levelno == logging.ERROR else Color.gold()
            embed = Embed(title=f"[{record.levelname}] Log Entry: {record.name}", description=formatted_message,
                          color=color)
            self.embed_buffer.append(embed)

            if record.levelno == logging.WARNING or record.levelno == logging.ERROR:
                if 'rate limited' in formatted_message:
                    return
                self.error_timestamps.append(datetime.utcnow())
                # Remove any timestamps older than 5 minutes
                self.error_timestamps = [timestamp for timestamp in self.error_timestamps if (datetime.utcnow() - timestamp).seconds < 300]
                # If there are more than 5 errors in the last 5 minutes, send a message to the error channel
                if len(self.error_timestamps) > 5:
                    os._exit(1)
        except Exception as e:
            print(f'Error sending log message: {e}')

    async def log_sender(self):
        while True:
            # If there is a log in the buffer
            if self.embed_buffer and self.client.statics.log_channel:
                # Send the first 10 embeds in a single message
                embeds_to_send = self.embed_buffer[:10]
                self.embed_buffer = self.embed_buffer[10:]
                message = ''
                # Send the embeds
                if len(embeds_to_send) == 10:
                    if any(embed.color == Color.red() or embed.color == Color.gold() for embed in embeds_to_send):
                        message = f'<@&1072596548636135435>'
                    await self.client.statics.log_channel.send(message, embeds=embeds_to_send)
                else:
                    for embed in embeds_to_send:
                        if embed.color == Color.red() or embed.color == Color.gold():
                            message = f'<@&1072596548636135435>'
                        await self.client.statics.log_channel.send(message, embed=embed)
                        message = ''
            await asyncio.sleep(10)
