import requests
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Class to handle Telegram notifications"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        
    def send_message(self, message: str, max_retries: int = 3) -> bool:
        """
        Send a message to the configured Telegram chat
        
        Args:
            message: Message text to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if message sent successfully, False otherwise
        """
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Sending Telegram message (attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Telegram request timeout (attempt {attempt + 1})")
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Telegram connection error (attempt {attempt + 1})")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Telegram request error: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error sending Telegram message: {e}")
                
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                import time
                time.sleep(2)
                
        logger.error(f"Failed to send Telegram message after {max_retries + 1} attempts")
        return False
        
    def test_connection(self) -> bool:
        """
        Test the Telegram bot connection
        
        Returns:
            True if connection is successful, False otherwise
        """
        url = f"{self.base_url}/getMe"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    logger.info(f"Telegram bot connected: {bot_info.get('username', 'Unknown')}")
                    return True
                else:
                    logger.error(f"Telegram bot test failed: {result.get('description', 'Unknown error')}")
            else:
                logger.error(f"Telegram bot test HTTP error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            
        return False
        
    def send_test_message(self) -> bool:
        """
        Send a test message to verify functionality
        
        Returns:
            True if test message sent successfully, False otherwise
        """
        test_message = "🧪 Test message from Ethereum Gas Monitor\n\nIf you received this, the bot is working correctly!"
        return self.send_message(test_message)

def start_gas_monitor():
    # Retrieve environment variables with debug logging
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    logger.info(f"TELEGRAM_BOT_TOKEN value: {bot_token or 'Not set'}")  # Debug log
    if not bot_token:
        logger.error("Failed to start gas monitor: TELEGRAM_BOT_TOKEN environment variable is required")
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    logger.info(f"TELEGRAM_CHAT_ID value: {chat_id or 'Not set'}")  # Debug log
    if not chat_id:
        logger.error("Failed to start gas monitor: TELEGRAM_CHAT_ID environment variable is required")
        raise ValueError("TELEGRAM_CHAT_ID is not set")
    
    # Initialize TelegramNotifier
    notifier = TelegramNotifier(bot_token, chat_id)

    # Test the connection
    if not notifier.test_connection():
        logger.error("Failed to connect to Telegram API")
        raise RuntimeError("Telegram bot connection failed")

    # Send a test message to verify
    if not notifier.send_test_message():
        logger.error("Failed to send test message")
        raise RuntimeError("Telegram test message failed")

    logger.info("Gas monitor started successfully")
    # Proceed with gas monitor logic...

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        start_gas_monitor()
    except Exception as e:
        logger.error(f"Gas monitor failed to start: {e}")
        raise
