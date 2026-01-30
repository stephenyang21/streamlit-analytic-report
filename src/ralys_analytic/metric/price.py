import os
import requests
from dotenv import load_dotenv

load_dotenv()


def getLatestTokenPrice(client,address:list[str]):

    price = client.prices.getCurrentPrices(address)['coins'][address[0]]['price']

    return price


def getRaylsPrice():
    """
    Get the latest Rayls (RLS) token price in USD from CoinMarketCap API.
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
        price_usd = rls_data["quote"]["USD"]["price"]
        return {
            "symbol": "RLS",
            "price_usd": price_usd,
            "market_cap": rls_data["quote"]["USD"].get("market_cap"),
            "volume_24h": rls_data["quote"]["USD"].get("volume_24h"),
            "percent_change_24h": rls_data["quote"]["USD"].get("percent_change_24h"),
        }
    else:
        raise Exception(f"Error fetching RLS price: {data.get('status', {}).get('error_message', 'Unknown error')}")