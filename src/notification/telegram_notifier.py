import json
import os
import urllib.request
import urllib.error
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
            print("Warning: Telegram notification skipped — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured.")
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
                if res.status == 200:
                    body = json.loads(res.read().decode('utf-8'))
                    if body.get("ok"):
                        return True
                    print(f"Warning: Telegram API responded with error: {body.get('description')}")
                    return False
        except urllib.error.HTTPError as e:
            # Fall back to plain text if Markdown format triggers bad request
            err_body = e.read().decode('utf-8', errors='replace')
            try:
                data = json.dumps({
                    "chat_id": self.chat_id,
                    "text": message
                }).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    if res.status == 200:
                        body = json.loads(res.read().decode('utf-8'))
                        if body.get("ok"):
                            return True
                        print(f"Warning: Telegram API responded with error: {body.get('description')}")
                        return False
            except urllib.error.HTTPError as fallback_err:
                fallback_body = fallback_err.read().decode('utf-8', errors='replace')
                print(f"Warning: Telegram notification failed (HTTP {fallback_err.code}): {fallback_body}")
                return False
            except Exception as fallback_ex:
                print(f"Warning: Telegram notification failed: {fallback_ex}")
                return False
        except Exception as e:
            # Fall back to plain text for any other formatting exceptions
            try:
                data = json.dumps({
                    "chat_id": self.chat_id,
                    "text": message
                }).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    if res.status == 200:
                        body = json.loads(res.read().decode('utf-8'))
                        if body.get("ok"):
                            return True
                        print(f"Warning: Telegram API responded with error: {body.get('description')}")
                        return False
            except Exception as fallback_e:
                print(f"Warning: Could not send Telegram notification: {fallback_e}")
                return False

        return False
