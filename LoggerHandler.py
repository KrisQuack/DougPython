import logging
import os
from logging import StreamHandler

from discord import Embed, Color, SyncWebhook


class LoggerHandler(logging.Handler):
    def __init__(self, webhook_url: str) -> None:
        super().__init__()
        self.webhook = SyncWebhook.from_url(webhook_url)  # Initialize webhook for Discord
        # Set a default formatter for log messages
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()  # Initialize a stream handler for terminal logging
        self.stream_handler.setFormatter(self.formatter)  # Set formatter for terminal logging
        self.warning_and_above_count = 0  # Initialize the counter for warning and above events

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = None  # Initialize message variable for @mention in Discord
            # Ignore logs from Azure's HTTP logging policy
            if record.name == "azure.core.pipeline.policies.http_logging_policy":
                return
            # Emit log record to terminal via stream handler
            self.stream_handler.emit(record)
            # Ignore logs containing "rate limited" to prevent spam
            if "rate limited" in record.msg or "successfully RESUMED session" in record.msg:
                return
            # Determine embed color based on log level
            if record.levelno == logging.ERROR:
                self.warning_and_above_count += 1  # Increment warning and above counter
                color = Color.red()
                message = '<@130062174918934528>'  # Send @mention in Discord for ERROR logs
            elif record.levelno == logging.WARNING:
                self.warning_and_above_count += 1  # Increment warning and above counter
                color = Color.gold()
            elif record.levelno == logging.INFO:
                color = Color.blue()
            else:
                color = Color.default()  # Use default color for other log levels
            # Use `record.getMessage()` to get the formatted message string
            formatted_message = record.getMessage()
            # Create Discord embed with log details
            embed = Embed(
                title=f"[{record.levelname}] Log Entry: {record.name}",
                description=formatted_message,
                color=color
            )
            embed.set_footer(text=record.asctime)  # Set footer to show log timestamp
            # Send log details to Discord via webhook
            self.webhook.send(content=message, embed=embed)
            # Reboot if there are more than 10 warning and above events
            if self.warning_and_above_count > 10:
                os._exit(1)
        except Exception as e:
            # Catch and print any exception that occurs while sending log to Discord
            print(f'Error sending log message: {e}')
