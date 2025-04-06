# APP/features/bots/bot_resp.py
import logging
from typing import Optional
from telegram.ext import ContextTypes
from telegram import Update, ChatPermissions
from Database.telegram_database import TDB_KEYS, TelegramDatabase
from ..Cyber import Cyber
from datetime import datetime, timedelta
import pytz
import asyncio
logger = logging.getLogger(__name__)


def get_telegram_until_date(hours: int, timezone: str = "Asia/Kolkata") -> int:
    """
    Get UTC timestamp for Telegram actions with timezone support
    
    Args:
        hours: Duration in hours (e.g., 1 for 1-hour mute)
        timezone: IANA timezone name (e.g., "America/New_York")
    
    Returns:
        Unix timestamp (seconds) for Telegram API
    """
    # Get current time in specified timezone
    tz = pytz.timezone(timezone)
    now_local = datetime.now(tz)
    
    # Calculate future time in local timezone
    future_local = now_local + timedelta(hours=int(hours))
    
    # Convert to UTC and get timestamp
    future_utc = future_local.astimezone(pytz.UTC)
    print(int(future_utc.timestamp()))
    return int(future_utc.timestamp())


async def mute_user(chat_id, user_id, update : Update, context: ContextTypes, timing : int):
    await update.message.reply_text(f"Your behavior has crossed the threshold of acceptable conduct. You've exceeded the warning limit, and as a result, you will be muted for {timing} hour(s).")
    until_date = get_telegram_until_date(timing)
    permissions = ChatPermissions.no_permissions()
    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=permissions,
        until_date=until_date
    )
    logging.info(f"Muted user {user_id} for {timing} hours")

async def kick_user(context, chat_id, user_id):
    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
    await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

async def ban_user(chat_id, user_id, update : Update, context: ContextTypes, timing : int, msg:str) -> None:
    await update.message.reply_text(msg)
    until_date = get_telegram_until_date(timing)
    
    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id, until_date=until_date)
    logging.info(f"Muted user {user_id} for {timing} hours")

async def handle_message(update: Update, context: ContextTypes, cyber: Cyber, tb : TelegramDatabase):
    """
    A message handler written to identify hate speech and controlling the group, This will be attached to TelegramBot class
    """

    chat_id = update.message.chat.id
    user_id = update.effective_user.id
    if not tb.getGroupSetting(chat_id, TDB_KEYS.PROTECTION_ENABLED):
        return
        
    administrators = await update.message.chat.get_administrators()


    admin_links = [
    f"t.me/{admin.user.username}"
    for admin in administrators if admin.user.username
    ]

    admin_ids = [
        admin.user.id 
        for admin in administrators if not admin.user.is_bot
    ]
    banMessage = tb.getGroupSetting(chat_id, TDB_KEYS.ADMIN_MESSAGE).replace("{Admins}", "\n".join(admin_links)).replace("{GroupName}", update.message.chat.title)

    numberOfTimesMuteable =  tb.getGroupSetting(chat_id, TDB_KEYS.MUTE_COUNT)
    muteDuration = tb.getGroupSetting(chat_id, TDB_KEYS.MUTE_DURATION)
    tb.ensure_user(chat_id, user_id) # Makes sure user is in db, if not creates one with default settings
    message_text = update.message.text

    if cyber.detect_hate_speech(message_text):
        wc = tb.getWarningCount(chat_id, user_id)
        if wc < 3:
            tb.warnUser(chat_id, user_id)
            await update.message.reply_text(tb.getGroupSetting(chat_id, TDB_KEYS.WARNING_MESSAGE).replace("{mute_times}", str(numberOfTimesMuteable)))
        else:
            mc = tb.getMutedCount(chat_id, user_id)
            if mc <= numberOfTimesMuteable:
                tb.mute_user(chat_id, user_id)
                await mute_user(chat_id, user_id, update, context, muteDuration)
            else:
                if tb.getGroupSetting(chat_id, TDB_KEYS.ALLOW_BANNING):
                    

                    # Reset settings after kicked/banned

                    if (repeat_action:=tb.getGroupSetting(chat_id, TDB_KEYS.REPEAT_ACTION)) == TDB_KEYS.BAN:

                        tb.toggleBan(chat_id, user_id)
                        await update.message.reply_text(banMessage)
                        await asyncio.sleep(10)
                        await ban_user(chat_id, user_id, update, context, timing=30*24, msg=banMessage)
                        tb.resetWarningCount(chat_id, user_id)
                        tb.resetMutedCount(chat_id, user_id)
                    elif repeat_action == TDB_KEYS.KICK:
                        await update.message.reply_text(banMessage+"\nYou have just been kicked out of the group. You can rejoin it if you agree to follow the group")
                        await asyncio.sleep(10)
                        await kick_user(context, chat_id, user_id)
                        tb.resetWarningCount(chat_id, user_id)
                        tb.resetMutedCount(chat_id, user_id)
                else:
                    tb.mute_user(chat_id, user_id)
                    await mute_user(chat_id, user_id, update, context, muteDuration)


