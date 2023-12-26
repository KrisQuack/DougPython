import asyncio
import logging
import os
import time
from logging import StreamHandler
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


class TelegramLogging(logging.Handler):
    def __init__(self, telegram_key: str) -> None:
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_handler = StreamHandler()
        self.stream_handler.setFormatter(self.formatter)
        
        # Setup telegram bot
        self.telegram_bot = telegram.Bot(telegram_key)
        self.telegram_app = ApplicationBuilder().token(telegram_key).build()
        
        # Initialize the log buffer
        self.log_buffer = []
        
    async def run_polling(self):
        # self.telegram_app.add_handler(CommandHandler("reboot", self.reboot_command))
        # await self.telegram_app.updater.initialize()
        # await self.telegram_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        asyncio.create_task(self.log_sender())
    

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name == "httpx":
                return

            self.stream_handler.emit(record)

            formatted_message = record.getMessage()
            formatted_message = formatted_message.replace('<', '&lt;').replace('>', '&gt;')
            formatted_message = f"<u><b>[{record.levelname}] Log Entry: {record.name}</b></u>\n<code>{formatted_message}</code>"
            self.log_buffer.append(formatted_message)
        except Exception as e:
            print(f'Error sending log message: {e}')
            
    async def reboot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Restart the bot"""
        if(update.message.from_user.id != 5397498524):
            return
        await update.message.reply_text("Rebooting...")
        os._exit(1)
        
        
    async def log_sender(self):
        while True:
            # If 10 seconds have passed since the last sent time and there are logs in the buffer
            if self.log_buffer:
                # Join all the logs in the buffer into a single message
                message = '\n\n'.join(self.log_buffer)
                # Clear the log buffer
                self.log_buffer = []
                # Check for errors
                if "ERROR" in message:
                    message = f"⚠️⚠️⚠️⚠️⚠️⚠️\n{message}"
                # Send the message
                await self.telegram_bot.send_message("5397498524", message, parse_mode='HTML')

            await asyncio.sleep(10)  # Sleep for a while