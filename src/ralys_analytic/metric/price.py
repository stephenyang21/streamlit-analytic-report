import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str):
    """Get secret from Streamlit secrets (production) or env var (local)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)

# Mapping from CoinGecko IDs to CoinMarketCap symbols
COINGECKO_TO_CMC_SYMBOL = {
    "zksync": "ZK",
    "plume": "PLUME",
    "avalanche-2": "AVAX",
    "ondo-finance": "ONDO",
    "ondo-us-dollar-yield": "USDY",
    "polygon-ecosystem-token": "POL",
    "chainlink": "LINK",
    "rls": "RLS",
}


def getCoinMarketCapPrice(symbol: str):
    """
    Get token price and price changes from CoinMarketCap API.

    Args:
        symbol: CoinMarketCap token symbol (e.g., "BTC", "ETH")

    Returns:
        Dictionary with current price and percent changes (24h, 7d, 30d)
    """
    api_key = get_secret("COINMARKET_API_KEY")
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }

    params = {
        "symbol": symbol,
        "convert": "USD",
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if response.status_code == 200 and "data" in data and symbol in data["data"]:
        token_data = data["data"][symbol]
        quote = token_data["quote"]["USD"]
        return {
            "price": quote.get("price"),
            "percent_change_24h": quote.get("percent_change_24h"),
            "percent_change_7d": quote.get("percent_change_7d"),
            "percent_change_30d": quote.get("percent_change_30d"),
        }
    else:
        error_msg = data.get("status", {}).get("error_message", "Unknown error")
        raise Exception(f"Error fetching price for {symbol}: {error_msg}")


def getCoinMarketCapPricesBatch(coingecko_ids: list[str]):
    """
    Get prices and price changes for multiple tokens in a single API call.
    Uses CoinMarketCap API with symbol mapping from CoinGecko IDs.

    Args:
        coingecko_ids: List of CoinGecko token IDs (for compatibility)

    Returns:
        Dictionary mapping CoinGecko token ID to price data
    """
    api_key = get_secret("COINMARKET_API_KEY")
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }

    # Map CoinGecko IDs to CoinMarketCap symbols
    symbols = []
    id_to_symbol = {}
    for cg_id in coingecko_ids:
        symbol = COINGECKO_TO_CMC_SYMBOL.get(cg_id)
        if symbol:
            symbols.append(symbol)
            id_to_symbol[cg_id] = symbol

    if not symbols:
        return {cg_id: {"price": None, "market_cap": None, "percent_change_24h": None, "percent_change_7d": None, "percent_change_30d": None} for cg_id in coingecko_ids}

    params = {
        "symbol": ",".join(symbols),
        "convert": "USD",
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if response.status_code != 200:
        error_msg = data.get("status", {}).get("error_message", "Unknown error")
        raise Exception(f"Error fetching prices from CoinMarketCap: {error_msg}")

    # Build results mapping back to CoinGecko IDs
    results = {}
    api_data = data.get("data", {})

    for cg_id in coingecko_ids:
        symbol = id_to_symbol.get(cg_id)
        if symbol and symbol in api_data:
            token_data = api_data[symbol]
            quote = token_data["quote"]["USD"]
            results[cg_id] = {
                "price": quote.get("price"),
                "market_cap": quote.get("market_cap"),
                "percent_change_24h": quote.get("percent_change_24h"),
                "percent_change_7d": quote.get("percent_change_7d"),
                "percent_change_30d": quote.get("percent_change_30d"),
            }
        else:
            results[cg_id] = {
                "price": None,
                "market_cap": None,
                "percent_change_24h": None,
                "percent_change_7d": None,
                "percent_change_30d": None,
            }

    return results


# Keep old function names as aliases for backwards compatibility
def getCoingeckoPrice(coingecko_id: str):
    """Alias for getCoinMarketCapPrice (uses symbol mapping)."""
    symbol = COINGECKO_TO_CMC_SYMBOL.get(coingecko_id)
    if not symbol:
        raise Exception(f"No CoinMarketCap symbol mapping for {coingecko_id}")
    return getCoinMarketCapPrice(symbol)


def getCoingeckoPricesBatch(coingecko_ids: list[str]):
    """Alias for getCoinMarketCapPricesBatch (uses symbol mapping)."""
    return getCoinMarketCapPricesBatch(coingecko_ids)


def getRaylsPrice():
    """
    Get the latest Rayls (RLS) token price in USD from CoinMarketCap API.
    Includes price changes for 24h, 7d, and 30d.
    """
    api_key = get_secret("COINMARKET_API_KEY")

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }

    parameters = {
        "symbol": "RLS",
        "convert": "USD"
    }

    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()

    if response.status_code == 200 and "data" in data:
        rls_data = data["data"]["RLS"]
        quote = rls_data["quote"]["USD"]
        return {
            "symbol": "RLS",
            "price_usd": quote["price"],
            "market_cap": quote.get("market_cap"),
            "volume_24h": quote.get("volume_24h"),
            "percent_change_24h": quote.get("percent_change_24h"),
            "percent_change_7d": quote.get("percent_change_7d"),
            "percent_change_30d": quote.get("percent_change_30d"),
        }
    else:
        raise Exception(f"Error fetching RLS price: {data.get('status', {}).get('error_message', 'Unknown error')}")


def getHistoricalPrices(coingecko_id: str, days: int = 30):
    """
    Get historical price data from CoinGecko (free tier supports historical data).

    Args:
        coingecko_id: CoinGecko token ID
        days: Number of days of historical data (max 365 for free tier)

    Returns:
        List of [timestamp, price] pairs or None if unavailable
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days,
    }
    if days > 90:
        params["interval"] = "daily"

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            return None

        return data.get("prices", [])

    except Exception:
        return None


def getHistoricalPricesBatch(token_configs: list, days: int = 30):
    """
    Get historical prices for multiple tokens from CoinGecko.

    Args:
        token_configs: List of dicts with 'coingecko_id' and 'name'
        days: Number of days of historical data

    Returns:
        Dictionary mapping token name to price series
    """
    import time

    results = {}

    for config in token_configs:
        coingecko_id = config.get("coingecko_id")
        name = config.get("name")

        try:
            prices = getHistoricalPrices(coingecko_id, days)
            if prices and len(prices) > 0:
                results[name] = prices
            # Add delay to avoid CoinGecko rate limiting (10-50 calls/min for free tier)
            time.sleep(1.5)
        except Exception:
            continue

    return results


def getRaylsHistoricalPrices(days: int = 30):  # noqa: ARG001
    """
    Get historical price data for Rayls from CoinMarketCap.

    Args:
        days: Number of days of historical data (unused - historical data requires paid plan)

    Returns:
        List of [timestamp, price] pairs or None if unavailable
    """
    api_key = get_secret("COINMARKET_API_KEY")

    if not api_key:
        return None

    # CoinMarketCap historical data requires a paid plan
    # For free tier, we'll return None and handle it in the dashboard
    # If you have a paid plan, you can use the /v2/cryptocurrency/quotes/historical endpoint

    return None