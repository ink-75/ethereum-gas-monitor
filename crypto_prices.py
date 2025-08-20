"""
Cryptocurrency price fetching functionality using CoinGecko API
"""

import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CryptoPriceFetcher:
    """Class to handle cryptocurrency price fetching via CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Ethereum Gas Monitor/1.0'
        })
        
    def get_eth_btc_prices(self, max_retries: int = 2, retry_delay: int = 3) -> Optional[Dict[str, float]]:
        """
        Fetch current ETH and BTC prices from CoinGecko API
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary with ETH and BTC prices in USD or None if failed
        """
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': 'bitcoin,ethereum',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Fetching crypto prices (attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract prices
                bitcoin_data = data.get('bitcoin', {})
                ethereum_data = data.get('ethereum', {})
                
                btc_price = bitcoin_data.get('usd')
                eth_price = ethereum_data.get('usd')
                btc_change = bitcoin_data.get('usd_24h_change', 0)
                eth_change = ethereum_data.get('usd_24h_change', 0)
                
                if btc_price is None or eth_price is None:
                    logger.error("Price data not found in API response")
                    if attempt < max_retries:
                        import time
                        time.sleep(retry_delay)
                        continue
                    return None
                
                result = {
                    'btc_price': float(btc_price),
                    'eth_price': float(eth_price),
                    'btc_change_24h': float(btc_change),
                    'eth_change_24h': float(eth_change)
                }
                
                logger.debug(f"Successfully fetched crypto prices: BTC ${btc_price:,.2f}, ETH ${eth_price:,.2f}")
                return result
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Crypto API request timeout (attempt {attempt + 1})")
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Crypto API connection error (attempt {attempt + 1})")
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"Crypto API HTTP error: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Crypto API request error: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching crypto prices: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
        logger.error(f"Failed to fetch crypto prices after {max_retries + 1} attempts")
        return None
        
    def format_price_change(self, change_24h: float) -> str:
        """
        Format 24h price change with appropriate emoji and color
        
        Args:
            change_24h: 24-hour price change percentage
            
        Returns:
            Formatted string with emoji and percentage
        """
        if change_24h > 0:
            return f"📈 +{change_24h:.2f}%"
        elif change_24h < 0:
            return f"📉 {change_24h:.2f}%"
        else:
            return f"➡️ {change_24h:.2f}%"