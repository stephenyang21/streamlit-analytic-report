import os
import requests
import streamlit as st
from dotenv import load_dotenv
from .holders import TOKEN_CONTRACTS

load_dotenv()

# Moralis API base URL
MORALIS_API_URL = "https://deep-index.moralis.io/api/v2.2"


def get_secret(key: str):
    """Get secret from Streamlit secrets (production) or env var (local)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)


def get_moralis_api_key():
    """Get Moralis API key from environment."""
    return get_secret("MORALIS_API_KEY")


def get_moralis_headers():
    """Get headers for Moralis API requests."""
    api_key = get_moralis_api_key()
    return {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }


def get_token_analytics(contract_address: str, chain: str = "eth"):
    """
    Get token analytics data from Moralis API.
    Returns trading volume, buyers/sellers, price changes, and liquidity data.

    Args:
        contract_address: Token contract address
        chain: Blockchain network (eth, polygon, bsc, avalanche, etc.)

    Returns:
        Dictionary with analytics data including:
        - totalBuyVolume (5m, 1h, 6h, 24h)
        - totalSellVolume (5m, 1h, 6h, 24h)
        - totalBuyers (5m, 1h, 6h, 24h)
        - totalSellers (5m, 1h, 6h, 24h)
        - totalBuys (5m, 1h, 6h, 24h)
        - totalSells (5m, 1h, 6h, 24h)
        - uniqueWallets (5m, 1h, 6h, 24h)
        - pricePercentChange (5m, 1h, 6h, 24h)
        - usdPrice
        - totalLiquidityUsd
        - totalFullyDilutedValuation
    """
    url = f"{MORALIS_API_URL}/tokens/{contract_address}/analytics?chain={chain}"

    try:
        response = requests.request("GET", url, headers=get_moralis_headers(), timeout=15)
        data = response.json()

        if response.status_code == 200:
            return data
        else:
            return {"error": data.get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}


def get_all_token_analytics():
    """
    Get analytics data for all configured tokens using Moralis API.

    Returns:
        Dictionary mapping token name to analytics data
    """
    results = {}

    for token_name, token_info in TOKEN_CONTRACTS.items():
        contract_address = token_info["address"]
        chain = token_info.get("chain", "eth")
        try:
            data = get_token_analytics(contract_address, chain)

            if "error" in data:
                results[token_name] = {
                    "contract_address": contract_address,
                    "chain": chain,
                    "total_buy_volume": None,
                    "total_sell_volume": None,
                    "total_buyers": None,
                    "total_sellers": None,
                    "total_buys": None,
                    "total_sells": None,
                    "unique_wallets": None,
                    "price_percent_change": None,
                    "usd_price": None,
                    "total_liquidity_usd": None,
                    "total_fdv": None,
                    "error": data.get("error"),
                }
            else:
                results[token_name] = {
                    "contract_address": contract_address,
                    "chain": chain,
                    "total_buy_volume": data.get("totalBuyVolume", {}),
                    "total_sell_volume": data.get("totalSellVolume", {}),
                    "total_buyers": data.get("totalBuyers", {}),
                    "total_sellers": data.get("totalSellers", {}),
                    "total_buys": data.get("totalBuys", {}),
                    "total_sells": data.get("totalSells", {}),
                    "unique_wallets": data.get("uniqueWallets", {}),
                    "price_percent_change": data.get("pricePercentChange", {}),
                    "usd_price": data.get("usdPrice"),
                    "total_liquidity_usd": data.get("totalLiquidityUsd"),
                    "total_fdv": data.get("totalFullyDilutedValuation"),
                }

        except Exception as e:
            results[token_name] = {
                "contract_address": contract_address,
                "chain": chain,
                "total_buy_volume": None,
                "total_sell_volume": None,
                "total_buyers": None,
                "total_sellers": None,
                "total_buys": None,
                "total_sells": None,
                "unique_wallets": None,
                "price_percent_change": None,
                "usd_price": None,
                "total_liquidity_usd": None,
                "total_fdv": None,
                "error": str(e),
            }

    return results


def get_all_token_analytics_cached():
    """
    Cache-aware version of get_all_token_analytics().
    Returns data from PostgreSQL cache if < 6 hours old,
    otherwise fetches from Moralis and updates cache.
    """
    from . import db_cache

    results = {}
    for token_name, token_info in TOKEN_CONTRACTS.items():
        contract_address = token_info["address"]
        chain = token_info.get("chain", "eth")

        try:
            raw = db_cache.get_or_fetch(
                data_type="analytics",
                token_name=token_name,
                contract_address=contract_address,
                chain=chain,
                fetch_fn=lambda ca=contract_address, ch=chain: get_token_analytics(ca, ch),
            )

            if "error" in raw:
                results[token_name] = {
                    "contract_address": contract_address,
                    "chain": chain,
                    "total_buy_volume": None,
                    "total_sell_volume": None,
                    "total_buyers": None,
                    "total_sellers": None,
                    "total_buys": None,
                    "total_sells": None,
                    "unique_wallets": None,
                    "price_percent_change": None,
                    "usd_price": None,
                    "total_liquidity_usd": None,
                    "total_fdv": None,
                    "error": raw.get("error"),
                }
            else:
                results[token_name] = {
                    "contract_address": contract_address,
                    "chain": chain,
                    "total_buy_volume": raw.get("totalBuyVolume", {}),
                    "total_sell_volume": raw.get("totalSellVolume", {}),
                    "total_buyers": raw.get("totalBuyers", {}),
                    "total_sellers": raw.get("totalSellers", {}),
                    "total_buys": raw.get("totalBuys", {}),
                    "total_sells": raw.get("totalSells", {}),
                    "unique_wallets": raw.get("uniqueWallets", {}),
                    "price_percent_change": raw.get("pricePercentChange", {}),
                    "usd_price": raw.get("usdPrice"),
                    "total_liquidity_usd": raw.get("totalLiquidityUsd"),
                    "total_fdv": raw.get("totalFullyDilutedValuation"),
                }
        except Exception as e:
            results[token_name] = {
                "contract_address": contract_address,
                "chain": chain,
                "total_buy_volume": None,
                "total_sell_volume": None,
                "total_buyers": None,
                "total_sellers": None,
                "total_buys": None,
                "total_sells": None,
                "unique_wallets": None,
                "price_percent_change": None,
                "usd_price": None,
                "total_liquidity_usd": None,
                "total_fdv": None,
                "error": str(e),
            }

    return results
