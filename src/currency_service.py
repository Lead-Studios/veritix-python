import logging
import requests
from typing import Dict, List, Optional
from cachetools import TTLCache, cached
from fastapi import HTTPException, status
from src.config import get_settings

logger = logging.getLogger("veritix.currency_service")

class ServiceUnavailableException(HTTPException):
    def __init__(self, detail: str = "Currency exchange service is currently unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

# Cache rates for 10 minutes (600 seconds)
rates_cache = TTLCache(maxsize=1, ttl=600)

@cached(cache=rates_cache)
def get_exchange_rates() -> Dict[str, float]:
    """Fetch latest exchange rates from external API relative to USD."""
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("rates", {})
    except Exception as exc:
        logger.error(f"Failed to fetch exchange rates: {exc}")
        raise ServiceUnavailableException()

def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
    """
    Get the exchange rate between two currencies.
    
    If from_currency is same as to_currency, returns 1.0.
    """
    if from_currency == to_currency:
        return 1.0
        
    supported = get_settings().SUPPORTED_CURRENCIES.split(",")
    if from_currency not in supported or to_currency not in supported:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Currency not supported. Supported: {supported}"
        )
        
    rates = get_exchange_rates()
    
    if from_currency not in rates or to_currency not in rates:
        logger.error(f"Currency {from_currency} or {to_currency} not found in FX rates")
        raise ServiceUnavailableException(detail="Exchange rate for requested currency not available")
        
    # Standardize to USD then to target
    # rate_to_usd = 1 / rates[from_currency] if from_currency != "USD" else 1.0
    # target_rate = rate_to_usd * rates[to_currency]
    
    # Simpler since API is based on USD:
    # 1 USD = rates[NGN] NGN
    # 1 USD = rates[GBP] GBP
    # 1 NGN = (1 / rates[NGN]) USD
    # 1 NGN = (1 / rates[NGN]) * rates[GBP] GBP
    
    usd_rate_for_from = rates[from_currency]
    usd_rate_for_to = rates[to_currency]
    
    return usd_rate_for_to / usd_rate_for_from
