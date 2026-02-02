import os
import requests
from dotenv import load_dotenv

load_dotenv()


def getCoingeckoPrice(coingecko_id: str):
    """
    Get token price and price changes from CoinGecko API.

    Args:
        coingecko_id: CoinGecko token ID (e.g., "bitcoin", "ethereum")

    Returns:
        Dictionary with current price and percent changes (24h, 7d, 30d)
    """
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": coingecko_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_7d_change": "true",
        "include_30d_change": "true",
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200 and coingecko_id in data:
        token_data = data[coingecko_id]
        return {
            "price": token_data.get("usd"),
            "percent_change_24h": token_data.get("usd_24h_change"),
            "percent_change_7d": token_data.get("usd_7d_change"),
            "percent_change_30d": token_data.get("usd_30d_change"),
        }
    else:
        raise Exception(f"Error fetching price for {coingecko_id}: {data}")


def getCoingeckoPricesBatch(coingecko_ids: list[str]):
    """
    Get prices and price changes for multiple tokens in a single API call.
    Uses /coins/markets endpoint to get 7d and 30d price changes.

    Args:
        coingecko_ids: List of CoinGecko token IDs

    Returns:
        Dictionary mapping token ID to price data
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "ids": ",".join(coingecko_ids),
        "vs_currency": "usd",
        "price_change_percentage": "24h,7d,30d",
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200:
        raise Exception(f"Error fetching prices from CoinGecko: {data}")

    # Build results from the list response
    results = {}
    data_by_id = {item["id"]: item for item in data} if isinstance(data, list) else {}

    for token_id in coingecko_ids:
        if token_id in data_by_id:
            token_data = data_by_id[token_id]
            results[token_id] = {
                "price": token_data.get("current_price"),
                "market_cap": token_data.get("market_cap"),
                "percent_change_24h": token_data.get("price_change_percentage_24h_in_currency"),
                "percent_change_7d": token_data.get("price_change_percentage_7d_in_currency"),
                "percent_change_30d": token_data.get("price_change_percentage_30d_in_currency"),
            }
        else:
            results[token_id] = {
                "price": None,
                "market_cap": None,
                "percent_change_24h": None,
                "percent_change_7d": None,
                "percent_change_30d": None,
            }

    return results


def getRaylsPrice():
    """
    Get the latest Rayls (RLS) token price in USD from CoinMarketCap API.
    Includes price changes for 24h, 7d, and 30d.
    """
    api_key = os.getenv("COINMARKET_API_KEY")

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
    Get historical price data from CoinGecko.

    Args:
        coingecko_id: CoinGecko token ID
        days: Number of days of historical data (max 365 for free tier)

    Returns:
        List of [timestamp, price] pairs
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily" if days > 90 else None,
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200:
        return None

    return data.get("prices", [])


def getHistoricalPricesBatch(token_configs: list, days: int = 30):
    """
    Get historical prices for multiple tokens.

    Args:
        token_configs: List of dicts with 'coingecko_id' and 'name'
        days: Number of days of historical data

    Returns:
        Dictionary mapping token name to normalized price series
    """
    import time

    results = {}

    for config in token_configs:
        coingecko_id = config.get("coingecko_id")
        name = config.get("name")

        if coingecko_id == "rls":
            # Skip Rayls for CoinGecko (will use CoinMarketCap)
            continue

        try:
            prices = getHistoricalPrices(coingecko_id, days)
            if prices and len(prices) > 0:
                results[name] = prices
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
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
    api_key = os.getenv("COINMARKET_API_KEY")

    if not api_key:
        return None

    # CoinMarketCap historical data requires a paid plan
    # For free tier, we'll return None and handle it in the dashboard
    # If you have a paid plan, you can use the /v2/cryptocurrency/quotes/historical endpoint

    return None