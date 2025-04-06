import threading
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes, ChatMemberHandler
from Database.telegram_database import TelegramDatabase
from typing import Callable, Optional
from telegram import Update
import logging
from ..Cyber import Cyber

class TelegramBot:
    """Thread-safe Telegram bot with start/stop in background thread"""
    _instance_lock = threading.Lock()
    _active_instance = None
    def __init__(self, token: str, message_handler=None, database: Optional[object] = None, cyber : Cyber=None):
        self.token = token
        self.message_handler = message_handler
        self.command_handlers = {}
        self._stop_event = threading.Event()
        self._thread = None
        self.database = database
        self.cyber = cyber
    
    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._active_instance is not None:
                raise RuntimeError("Only one bot instance allowed")
            cls._active_instance = super().__new__(cls)
            return cls._active_instance
    def command(self, name: str):
        """Decorator to add commands like /start"""
        def decorator(func):
            self.command_handlers[name] = func
            return func
        return decorator

    async def check_membership_safe(self, chat_id: int) -> bool:
        """Check if bot is still a member of the chat"""
        try:
            member = await self.app.bot.get_chat_member(chat_id, self.app.bot.id)
            return member.status in ['creator', 'member','administrator']
        except Exception as e:
            logging.warning(f"Membership check failed for {chat_id}: {str(e)}")
            return False

    async def _handle_chat_member_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot being added/removed from groups/channels"""
        if not update.my_chat_member:
            return
            
        old_status = update.my_chat_member.old_chat_member.status
        new_status = update.my_chat_member.new_chat_member.status
        chat = update.my_chat_member.chat
        adder_id = update.my_chat_member.from_user.id

        # Skip private chats
        if chat.type == "private":
            return

        # Handle bot being added to group
        if (old_status != "member" or old_status != 'administrator') and (new_status == "member" or new_status == "administrator"):
            await self._handle_bot_added(chat, adder_id)
            
        # Handle bot being removed from group
        elif (old_status == "member" or old_status == "administrator") and (new_status != "member" or new_status != 'administrator'):
            await self._handle_bot_removed(chat)

    async def _handle_bot_added(self, chat, adder_id):
        """Process bot being added to a group/channel"""
        # Get adder's UUID from database
        adder_uuid = self.database.get_uuid(adder_id) if self.database else None

        if not adder_uuid or not self.database.is_verified(adder_id):
            # Unverified user flow
            await self.app.bot.send_message(
                chat_id=chat.id,
                text="🔒 Verification Required\n\n"
                    "Please register at our website first!\n"
                    "Then re-add me after verification."
            )
            await self.app.bot.leave_chat(chat.id)
            logging.warning(f"Left chat {chat.id} - Unverified adder {adder_id}")
        else:
            try:
                success = self.database.add_group_information(
                    chat_id=chat.id,
                    chat_title=chat.title,
                    chat_type=chat.type,
                    adder_telegram_id=adder_id,
                    uuid=adder_uuid
                )
                
                if success:
                    await self.app.bot.send_message(
                        chat_id=chat.id,
                        text="✅ Bot activated!\n\n"
                            "Configuration saved.\nSettings can be customized on our website.\nPlease give me Administration Permissions, I cannot work without it."
                    )
                    logging.info(f"Added to {chat.title} (ID: {chat.id}) by {adder_id}")
                else:
                    await self.app.bot.send_message(
                        chat_id=chat.id,
                        text="⚙️ Bot re-added - Existing settings preserved"
                    )

            except Exception as e:
                logging.error(f"Database error for chat {chat.id}: {str(e)}")
                await self.app.bot.send_message(
                    chat_id=chat.id,
                    text="⚠️ Configuration failed. Contact support."
                )
                await self.app.bot.leave_chat(chat.id)

    async def _handle_bot_removed(self, chat):
        """Process bot being removed from a group/channel"""
        try:
            if self.database:
                # Remove group from database
                removed = self.database.remove_group(chat.id)
                if removed:
                    logging.info(f"Bot removed from {chat.title} (ID: {chat.id}) - Database updated")
                else:
                    logging.info(f"Bot removed from {chat.title} (ID: {chat.id}) - No record in database")
        except Exception as e:
            logging.error(f"Error handling bot removal from {chat.id}: {str(e)}")

    async def _handle_message(self, update, context):
        """Route messages to handlers"""
        if update.message.text.startswith('/'):
            command = update.message.text.split()[0][1:]
            if command in self.command_handlers:
                await self.command_handlers[command](update, context)
        elif self.message_handler:
            print("Came here 1")
            print("*"*1000)
            await self.message_handler(update, context, self.cyber, self.database)

    def _run_in_thread(self):
        """Main bot loop running in background thread"""
        if hasattr(self, '_running') and self._running:
            logging.warning("Bot is already running!")
            return
        
        self._running = True
        async def _async_main():
            self.app = Application.builder().token(self.token).build()
            
            # Register handlers
            for cmd, handler in self.command_handlers.items():
                self.app.add_handler(CommandHandler(cmd, handler))
                
            self.app.add_handler(MessageHandler(filters.TEXT, self._handle_message))
            self.app.add_handler(
                ChatMemberHandler(self._handle_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER)
            )
            
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