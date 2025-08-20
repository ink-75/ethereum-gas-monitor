"""
Gas price monitoring functionality using Etherscan API
"""

import requests
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GasMonitor:
    """Class to handle Ethereum gas price monitoring via Etherscan API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
        self.session = requests.Session()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Ethereum Gas Monitor/1.0'
        })
        
    def get_current_gas_price(self, max_retries: int = 3, retry_delay: int = 5) -> Optional[float]:
        """
        Fetch current gas price from Etherscan API with retry logic
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Current gas price in gwei or None if failed
        """
        url = self.base_url
        params = {
            'module': 'gastracker',
            'action': 'gasoracle',
            'apikey': self.api_key
        }
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Fetching gas price (attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') != '1':
                    logger.error(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return None
                    
                result = data.get('result', {})
                
                # Get standard gas price (you can also use 'SafeGasPrice' or 'FastGasPrice')
                gas_price = result.get('ProposeGasPrice')
                
                if gas_price is None:
                    logger.error("Gas price not found in API response")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return None
                    
                try:
                    gas_price_float = float(gas_price)
                    logger.debug(f"Successfully fetched gas price: {gas_price_float} gwei")
                    return gas_price_float
                except ValueError:
                    logger.error(f"Invalid gas price format: {gas_price}")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching gas price: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                    
        logger.error(f"Failed to fetch gas price after {max_retries + 1} attempts")
        return None
        
    def get_detailed_gas_prices(self) -> Optional[dict]:
        """
        Get detailed gas price information including safe, standard, and fast prices
        
        Returns:
            Dictionary with gas price details or None if failed
        """
        url = self.base_url
        params = {
            'module': 'gastracker',
            'action': 'gasoracle',
            'apikey': self.api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != '1':
                logger.error(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                return None
                
            result = data.get('result', {})
            
            return {
                'safe': float(result.get('SafeGasPrice', 0)),
                'standard': float(result.get('ProposeGasPrice', 0)),
                'fast': float(result.get('FastGasPrice', 0))
            }
            
        except Exception as e:
            logger.error(f"Error fetching detailed gas prices: {e}")
            return None
