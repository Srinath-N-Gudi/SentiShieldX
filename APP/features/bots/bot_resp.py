# APP/features/bots/bot_resp.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def response_generator(
    username: str,
    message_text: str,
    user_id: int,
    chat_id: int,
    is_group: bool
) -> Optional[str]:
    """Basic response generator for Telegram bot"""
    try:
        msg = message_text.lower()
        
        if any(g in msg for g in ['hello', 'hi', 'hey']):
            return f"Hello @{username}! How can I help?"
            
        elif 'help' in msg:
            return ("Need help? Here's what I can do:\n"
                   "- Register your account with /register\n"
                   "- Verify with /verify\n"
                   "- Get help with /help")
                   
        return None
        
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return None