import os
from typing import Optional

from telegram import Bot


def send_telegram(text: str) -> Optional[str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return None
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=text[:4000])
        return "sent"
    except Exception:
        return None
