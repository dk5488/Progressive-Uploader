import pytest
from unittest.mock import patch, Mock
import io
import urllib.error
from src.notification.telegram_notifier import TelegramNotifier

def test_telegram_notifier_missing_credentials(capsys):
    notifier = TelegramNotifier(token="", chat_id="")
    result = notifier.send_message("Test message")
    assert result is False
    captured = capsys.readouterr()
    assert "Telegram notification skipped" in captured.out

def test_telegram_notifier_success():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"ok": true, "result": {}}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_urlopen.return_value = mock_response
        
        notifier = TelegramNotifier(token="test_token", chat_id="12345")
        result = notifier.send_message("Hello world")
        assert result is True

def test_telegram_notifier_http_error(capsys):
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.telegram.org",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(b'{"ok": false, "description": "Chat not found"}')
        )
        
        notifier = TelegramNotifier(token="test_token", chat_id="12345")
        result = notifier.send_message("Hello world")
        assert result is False
        captured = capsys.readouterr()
        assert "Chat not found" in captured.out or "Telegram notification failed" in captured.out
