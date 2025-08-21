#!/usr/bin/env python3
"""
Ethereum Gas Price Monitor
Main entry point for the gas price monitoring application.
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone, timedelta
from gas_monitor import GasMonitor
from telegram_notifier import TelegramNotifier
from crypto_prices import CryptoPriceFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gas_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class GasPriceAlert:
    def __init__(self):
        env_vars = os.environ
        logger.info(f"Available environment variables: {list(env_vars.keys())}")
        
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.telegram_bot_token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.telegram_chat_id:
            logger.error("TELEGRAM_CHAT_ID environment variable is required")
            raise ValueError("TELEGRAM_CHAT_ID is not set")
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
        if not self.etherscan_api_key:
            logger.error("ETHERSCAN_API_KEY environment variable is required")
            raise ValueError("ETHERSCAN_API_KEY is not set")
        gas_threshold_env = os.getenv("GAS_THRESHOLD")
        if not gas_threshold_env:
            logger.error("GAS_THRESHOLD environment variable is required")
            raise ValueError("GAS_THRESHOLD is not set")
        self.gas_threshold = float(gas_threshold_env)
        logger.info(f"GAS_THRESHOLD value from environment: {gas_threshold_env}")
        logger.info(f"ETHERSCAN_API_KEY value: {self.etherscan_api_key}")
        
        self.check_interval = int(os.getenv("CHECK_INTERVAL"))
        logger.info(f"CHECK_INTERVAL value from environment: {self.check_interval}")
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN"))
        logger.info(f"ALERT_COOLDOWN value from environment: {self.alert_cooldown}")
        self.moscow_timezone_offset = int(os.getenv("MOSCOW_TIMEZONE_OFFSET"))
        logger.info(f"MOSCOW_TIMEZONE_OFFSET value from environment: {self.moscow_timezone_offset}")
        self.silence_start_hour = int(os.getenv("SILENCE_START_HOUR"))
        logger.info(f"SILENCE_START_HOUR value from environment: {self.silence_start_hour}")
        self.silence_end_hour = int(os.getenv("SILENCE_END_HOUR"))
        logger.info(f"SILENCE_END_HOUR value from environment: {self.silence_end_hour}")

        self.gas_monitor = GasMonitor(self.etherscan_api_key)
        self.telegram_notifier = TelegramNotifier(self.telegram_bot_token, self.telegram_chat_id)
        self.crypto_fetcher = CryptoPriceFetcher()
        self.running = True
        self.last_alert_time = None
        
    def signal_handler(self, signum, frame):
        logger.info("Received shutdown signal. Stopping gas monitor...")
        self.running = False
        
    def is_silence_hours(self):
        moscow_tz = timezone(timedelta(hours=self.moscow_timezone_offset))
        moscow_time = datetime.now(moscow_tz)
        current_hour = moscow_time.hour
        
        start_hour = self.silence_start_hour
        end_hour = self.silence_end_hour
        
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:
            return current_hour >= start_hour or current_hour < end_hour
    
    def should_send_alert(self, gas_price):
        if gas_price > self.gas_threshold:
            return False
            
        if self.is_silence_hours():
            logger.info("Within silence hours - notification suppressed")
            return False
            
        if self.last_alert_time:
            time_since_last = datetime.now() - self.last_alert_time
            if time_since_last.total_seconds() < self.alert_cooldown:
                return False
                
        return True
        
    def format_gas_price_message(self, gas_price, threshold):
        message = (
            f"🔥 Gas Alert! 🔥\n\n"
            f"⛽ Gas Price: {gas_price} gwei\n"
            f"🎯 Your Threshold: {threshold} gwei\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        
        crypto_prices = self.crypto_fetcher.get_eth_btc_prices()
        if crypto_prices:
            btc_change = self.crypto_fetcher.format_price_change(crypto_prices['btc_change_24h'])
            eth_change = self.crypto_fetcher.format_price_change(crypto_prices['eth_change_24h'])
            
            message += (
                f"💰 Current Prices:\n"
                f"₿ BTC: ${crypto_prices['btc_price']:,.0f} {btc_change}\n"
                f"🔷 ETH: ${crypto_prices['eth_price']:,.2f} {eth_change}\n\n"
            )
        else:
            logger.warning("Could not fetch crypto prices for alert message")
            
        message += f"Perfect time to make transactions! ⛽"
        return message
        
    def run_check(self):
        try:
            logger.info("Checking gas prices...")
            gas_price = self.gas_monitor.get_current_gas_price()
            
            if gas_price is None:
                logger.warning("Failed to fetch gas price")
                return
                
            logger.info(f"Current gas price: {gas_price} gwei | Threshold: {self.gas_threshold}")
            
            status = "🟢 BELOW" if gas_price <= self.gas_threshold else "🔴 ABOVE"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Gas: {gas_price} gwei | Status: {status} threshold")
            
            if self.should_send_alert(gas_price):
                message = self.format_gas_price_message(gas_price, self.gas_threshold)
                logger.info(f"Attempting to send Telegram message: {message}")
                if self.telegram_notifier.send_message(message):
                    self.last_alert_time = datetime.now()
                    logger.info(f"Alert sent! Gas price {gas_price} gwei is below threshold {self.gas_threshold} gwei")
                else:
                    logger.error("Failed to send Telegram alert")
                    
        except Exception as e:
            logger.error(f"Error during gas price check: {str(e)}")
            
    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Starting Ethereum Gas Price Monitor")
        logger.info(f"Monitoring threshold: {self.gas_threshold} gwei")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Alert cooldown: {self.alert_cooldown} seconds")
        logger.info(f"Silence hours: {self.silence_start_hour}:00-{self.silence_end_hour}:00 Moscow time")
        
        startup_message = (
            f"🚀 Gas Monitor Started!\n\n"
            f"Threshold: {self.gas_threshold} gwei\n"
            f"Check Interval: {self.check_interval}s\n"
            f"Silence Hours: {self.silence_start_hour}:00-{self.silence_end_hour}:00 Moscow time\n"
            f"Monitoring started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Attempting to send startup message: {startup_message}")
        self.telegram_notifier.send_message(startup_message)
        
        while self.running:
            try:
                self.run_check()
                
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                time.sleep(10)
                
        logger.info("Gas price monitor stopped")

def main():
    try:
        monitor = GasPriceAlert()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start gas monitor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
