import asyncio
import logging
from logging import StreamHandler
import telegram


class TelegramLogging(logging.Handler):
    def __init__(self, telegram_key: str) -> None:
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()
        self.stream_handler.setFormatter(self.formatter)
        
        # Setup telegram bot
        self.telegram_bot = telegram.Bot(telegram_key)
        
        # Initialize the log buffer
        self.log_buffer = []
        
    async def run_polling(self):
        asyncio.create_task(self.log_sender())
    

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name == "httpx":
                return

            self.stream_handler.emit(record)
            
            # If it is warning or above, send the log to telegram
            if record.levelno >= logging.WARNING:
                formatted_message = record.getMessage()
                formatted_message = formatted_message.replace('<', '&lt;').replace('>', '&gt;')
                formatted_message = f"<u><b>[{record.levelname}] Log Entry: {record.name}</b></u>\n<code>{formatted_message}</code>"
                self.log_buffer.append(formatted_message)
        except Exception as e:
            print(f'Error sending log message: {e}')
        
    async def log_sender(self):
        while True:
            # If there is a log in the buffer
            if self.log_buffer:
                message = ''
                # While the message is less than 4000 characters
                while self.log_buffer and len(message + self.log_buffer[0]) <= 4000:
                    # Add the next log to the message
                    message += self.log_buffer.pop(0) + '\n\n'
                # Send the message
                await self.telegram_bot.send_message("5397498524", message, parse_mode='HTML')
            await asyncio.sleep(10)