"""
Configuration management for the Ethereum Gas Price Monitor
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class to manage all settings"""
    
    def __init__(self):
        # API Keys
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY", "YourApiKeyToken")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # Gas price settings
        self.gas_threshold = float(os.getenv("GAS_THRESHOLD", "1"))  # gwei
        
        # Timing settings
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "300"))  # seconds (5 minutes)
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN", "1800"))  # seconds (30 minutes)
        
        # Silence hours settings (Moscow time)
        self.silence_start_hour = int(os.getenv("SILENCE_START_HOUR", "0"))  # 0am Moscow time
        self.silence_end_hour = int(os.getenv("SILENCE_END_HOUR", "7"))  # 7am Moscow time
        self.moscow_timezone_offset = int(os.getenv("MOSCOW_TIMEZONE_OFFSET", "3"))  # UTC+3
        
        # API settings
        self.etherscan_base_url = "https://api.etherscan.io/api"
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))  # seconds
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "5"))  # seconds
        
        # Validate required settings
        self.validate_config()
        
    def validate_config(self):
        """Validate that required configuration is present"""
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
            
        if not self.telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
            
        if self.gas_threshold <= 0:
            raise ValueError("GAS_THRESHOLD must be greater than 0")
            
        if self.check_interval < 60:
            raise ValueError("CHECK_INTERVAL should be at least 60 seconds to avoid API rate limits")
