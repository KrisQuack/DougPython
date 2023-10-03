import logging
from logging import StreamHandler

from discord import Embed, Color, SyncWebhook


class LoggerHandler(logging.Handler):
    def __init__(self, webhook_url: str) -> None:
        super().__init__()
        self.webhook = SyncWebhook.from_url(webhook_url)
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()
        self.stream_handler.setFormatter(self.formatter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = None
            if record.name == "azure.core.pipeline.policies.http_logging_policy":
                return
            self.stream_handler.emit(record)
            if "rate limited" in record.msg:
                return
            if record.levelno == logging.ERROR:
                color = Color.red()
                message = '<@130062174918934528>'
            elif record.levelno == logging.WARNING:
                color = Color.gold()
            elif record.levelno == logging.INFO:
                color = Color.blue()
            else:
                color = Color.default()

            embed = Embed(title=f"[{record.levelname}] Log Entry: {record.name}", description=record.msg, color=color)
            embed.set_footer(text=record.asctime)
            self.webhook.send(content=message, embed=embed)
        except Exception as e:
            print(f'Error sending log message: {e}')
