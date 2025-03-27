import threading
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from typing import Callable, Optional

class TelegramBot:
    """Thread-safe Telegram bot with start/stop in background thread"""
    
    def __init__(self, token: str, message_handler: Optional[Callable] = None):
        self.token = token
        self.message_handler = message_handler
        self.command_handlers = {}
        self._stop_event = threading.Event()
        self._thread = None

    def command(self, name: str):
        """Decorator to add commands like /start"""
        def decorator(func):
            self.command_handlers[name] = func
            return func
        return decorator

    async def _handle_message(self, update, context):
        """Route messages to handlers"""
        if update.message.text.startswith('/'):
            command = update.message.text.split()[0][1:]
            if command in self.command_handlers:
                await self.command_handlers[command](update, context)
        elif self.message_handler:
            await self.message_handler(update)

    def _run_in_thread(self):
        """Main bot loop running in background thread"""
        async def _async_main():
            self.app = Application.builder().token(self.token).build()
            
            # Register handlers
            for cmd, handler in self.command_handlers.items():
                self.app.add_handler(CommandHandler(cmd, handler))
            self.app.add_handler(MessageHandler(filters.TEXT, self._handle_message))
            
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # Run until stop signal
            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)
            
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

        asyncio.run(_async_main())

    def start(self):
        """Start bot in background thread"""
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the bot gracefully"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)