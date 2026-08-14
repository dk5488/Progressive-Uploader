import json
import os
import urllib.request
from typing import Optional
from src.utils.env_loader import load_env

class TelegramNotifier:
    """Sends release status summary notifications to Telegram."""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        load_env()
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    def send_message(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Try Markdown formatting first
        try:
            data = json.dumps({
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=15) as res:
                return res.status == 200
        except Exception:
            # Fall back to plain text if markdown formatting raises syntax errors
            try:
                data = json.dumps({
                    "chat_id": self.chat_id,
                    "text": message
                }).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    return res.status == 200
            except Exception as e:
                print(f"Warning: Could not send Telegram notification: {e}")
                return False
