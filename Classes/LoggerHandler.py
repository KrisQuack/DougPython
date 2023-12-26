import logging
import os
import time
from logging import StreamHandler
from discord import Embed, Color, SyncWebhook

class LoggerHandler(logging.Handler):
    def __init__(self, webhook_url: str) -> None:
        super().__init__()
        self.webhook = SyncWebhook.from_url(webhook_url)
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()
        self.stream_handler.setFormatter(self.formatter)
        self.warning_and_above_timestamps = []  # List to store timestamps of warnings/errors

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name == "azure.core.pipeline.policies.http_logging_policy" or record.name == "sqlalchemy.engine.Engine":
                return

            self.stream_handler.emit(record)

            if "rate limited" in record.msg or "successfully RESUMED session" in record.msg:
                return

            color, message = self.determine_log_level(record)

            formatted_message = record.getMessage()
            embed = Embed(
                title=f"[{record.levelname}] Log Entry: {record.name}",
                description=formatted_message,
                color=color
            )
            embed.set_footer(text=record.asctime)
            self.webhook.send(content=message, embed=embed)

            self.check_and_reboot_if_needed()
        except Exception as e:
            print(f'Error sending log message: {e}')

    def determine_log_level(self, record: logging.LogRecord):
        message = None
        if record.levelno >= logging.WARNING:  # For WARNING and ERROR levels
            self.warning_and_above_timestamps.append(time.time())
            if record.levelno == logging.ERROR:
                color = Color.red()
                message = '<@130062174918934528>'
            else:
                color = Color.gold()
        elif record.levelno == logging.INFO:
            color = Color.blue()
        else:
            color = Color.default()
        return color, message

    def check_and_reboot_if_needed(self):
        one_hour_ago = time.time() - 3600
        # Filter out timestamps older than 1 hour
        self.warning_and_above_timestamps = [t for t in self.warning_and_above_timestamps if t > one_hour_ago]
        if len(self.warning_and_above_timestamps) >= 5:
            os._exit(1)