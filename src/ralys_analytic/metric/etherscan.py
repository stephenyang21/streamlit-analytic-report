import os
import time
import requests
import streamlit as st
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from .holders import TOKEN_CONTRACTS

load_dotenv()

# Etherscan API V2 base URL
ETHERSCAN_API_URL = "https://api.etherscan.io/v2"

# Known exchange hot wallet addresses (lowercase)
KNOWN_EXCHANGE_ADDRESSES = {
    "Binance": [
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
    ],
    "Coinbase": [
        "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        "0x503828976d22510aad0201ac7ec88293211d23da",
        "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43",
    ],
    "Kraken": [
        "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
        "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
    ],
}

# Flatten exchange addresses for quick lookup
_EXCHANGE_LOOKUP = {}
for exchange_name, addrs in KNOWN_EXCHANGE_ADDRESSES.items():
    for addr in addrs:
        _EXCHANGE_LOOKUP[addr.lower()] = exchange_name

# Chain ID mapping for Etherscan API V2
CHAIN_IDS = {
    "eth": 1,
    "polygon": 137,
    "bsc": 56,
    "avalanche": 43114,
    "arbitrum": 42161,
    "optimism": 10,
}


def get_secret(key: str):
    """Get secret from Streamlit secrets (production) or env var (local)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)


def get_etherscan_api_key():
    """Get Etherscan API key from environment."""
    return get_secret("ETHERSCAN_API_KEY")


def _fetch_token_transfers(contract_address, chain, start_timestamp, end_timestamp, max_pages=5):
    """
    Fetch token transfer events from Etherscan API V2 with pagination.

    Args:
        contract_address: Token contract address
        chain: Chain identifier (eth, polygon, etc.)
        start_timestamp: Unix timestamp for start of range
        end_timestamp: Unix timestamp for end of range
        max_pages: Maximum number of pages to fetch (10000 results per page)

    Returns:
        List of transfer dicts or {"error": str}
    """
    api_key = get_etherscan_api_key()
    if not api_key:
        return {"error": "ETHERSCAN_API_KEY not configured"}

    chain_id = CHAIN_IDS.get(chain, 1)
    all_transfers = []
    page = 1

    try:
        while page <= max_pages:
            params = {
                "chainid": chain_id,
                "module": "account",
                "action": "tokentx",
                "contractaddress": contract_address,
                "page": page,
                "offset": 10000,
                "sort": "desc",
                "apikey": api_key,
            }

            response = requests.get(ETHERSCAN_API_URL, params=params, timeout=30)
            data = response.json()

            if data.get("status") != "1" or not data.get("result"):
                if page == 1 and data.get("message") == "No transactions found":
                    return []
                break

            results = data["result"]
            if isinstance(results, str):
                if page == 1:
                    return {"error": results}
                break

            # Post-filter by timestamp
            filtered = []
            for tx in results:
                tx_ts = int(tx.get("timeStamp", 0))
                if start_timestamp <= tx_ts <= end_timestamp:
                    filtered.append(tx)
                elif tx_ts < start_timestamp:
                    # Results are sorted desc, so we can stop early
                    all_transfers.extend(filtered)
                    return all_transfers

            all_transfers.extend(filtered)

            if len(results) < 10000:
                break

            page += 1
            time.sleep(0.22)  # Rate limit

        return all_transfers

    except Exception as e:
        return {"error": str(e)}


def get_token_transfer_activity(contract_address, chain, days=30):
    """
    Aggregate token transfers into daily activity metrics.

    Returns:
        {
            "daily_stats": [{"date": ..., "transfer_count": ..., "unique_addresses": ..., "total_volume": ..., "avg_transfer_size": ...}],
            "large_transfers": [{"hash": ..., "from": ..., "to": ..., "value": ..., "timestamp": ...}],
            "summary": {"total_transfers": ..., "total_unique_addresses": ..., "total_volume": ..., "avg_daily_transfers": ...}
        }
    """
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    start_ts = int(start.timestamp())
    end_ts = int(now.timestamp())

    transfers = _fetch_token_transfers(contract_address, chain, start_ts, end_ts)

    if isinstance(transfers, dict) and "error" in transfers:
        return transfers
    if not transfers:
        return {
            "daily_stats": [],
            "large_transfers": [],
            "summary": {"total_transfers": 0, "total_unique_addresses": 0, "total_volume": 0, "avg_daily_transfers": 0},
        }

    # Parse transfers and bucket by day
    daily_buckets = defaultdict(lambda: {"transfers": [], "addresses": set(), "volume": 0.0})

    all_values = []
    for tx in transfers:
        try:
            decimals = int(tx.get("tokenDecimal", 18))
            value = int(tx.get("value", 0)) / (10 ** decimals)
            tx_ts = int(tx.get("timeStamp", 0))
            date_str = datetime.utcfromtimestamp(tx_ts).strftime("%Y-%m-%d")

            daily_buckets[date_str]["transfers"].append(tx)
            daily_buckets[date_str]["addresses"].add(tx.get("from", "").lower())
            daily_buckets[date_str]["addresses"].add(tx.get("to", "").lower())
            daily_buckets[date_str]["volume"] += value
            all_values.append(value)
        except (ValueError, TypeError):
            continue

    # Build daily stats
    daily_stats = []
    for date_str in sorted(daily_buckets.keys()):
        bucket = daily_buckets[date_str]
        count = len(bucket["transfers"])
        daily_stats.append({
            "date": date_str,
            "transfer_count": count,
            "unique_addresses": len(bucket["addresses"]),
            "total_volume": round(bucket["volume"], 2),
            "avg_transfer_size": round(bucket["volume"] / count, 2) if count > 0 else 0,
        })

    # Large transfers (top 95th percentile)
    large_transfers = []
    if all_values:
        import numpy as np
        threshold = np.percentile(all_values, 95)

        for tx in transfers:
            try:
                decimals = int(tx.get("tokenDecimal", 18))
                value = int(tx.get("value", 0)) / (10 ** decimals)
                if value >= threshold:
                    tx_ts = int(tx.get("timeStamp", 0))
                    large_transfers.append({
                        "hash": tx.get("hash", ""),
                        "from": tx.get("from", ""),
                        "to": tx.get("to", ""),
                        "value": round(value, 2),
                        "timestamp": datetime.utcfromtimestamp(tx_ts).strftime("%Y-%m-%d %H:%M"),
                    })
            except (ValueError, TypeError):
                continue

        large_transfers.sort(key=lambda x: x["value"], reverse=True)
        large_transfers = large_transfers[:50]

    # Summary
    all_addresses = set()
    for bucket in daily_buckets.values():
        all_addresses.update(bucket["addresses"])

    total_volume = sum(b["volume"] for b in daily_buckets.values())
    total_transfers = sum(len(b["transfers"]) for b in daily_buckets.values())

    summary = {
        "total_transfers": total_transfers,
        "total_unique_addresses": len(all_addresses),
        "total_volume": round(total_volume, 2),
        "avg_daily_transfers": round(total_transfers / max(len(daily_buckets), 1), 1),
    }

    return {
        "daily_stats": daily_stats,
        "large_transfers": large_transfers,
        "summary": summary,
    }


def get_all_token_transfer_activity(days=30):
    """
    Get transfer activity for all configured tokens.

    Returns:
        Dictionary mapping token name to activity data
    """
    results = {}

    for token_name, token_info in TOKEN_CONTRACTS.items():
        contract_address = token_info["address"]
        chain = token_info.get("chain", "eth")
        try:
            data = get_token_transfer_activity(contract_address, chain, days=days)
            results[token_name] = data
        except Exception as e:
            results[token_name] = {"error": str(e)}

    return results


def get_whale_transfers(contract_address, chain, min_tokens, limit=50):
    """
    Fetch recent large transfers above a minimum token threshold.

    Args:
        contract_address: Token contract address
        chain: Chain identifier
        min_tokens: Minimum token amount to qualify as a whale transfer
        limit: Maximum number of transfers to return

    Returns:
        List of whale transfer dicts sorted by value descending
    """
    now = datetime.utcnow()
    start = now - timedelta(days=30)
    start_ts = int(start.timestamp())
    end_ts = int(now.timestamp())

    transfers = _fetch_token_transfers(contract_address, chain, start_ts, end_ts, max_pages=3)

    if isinstance(transfers, dict) and "error" in transfers:
        return transfers
    if not transfers:
        return []

    whale_transfers = []
    for tx in transfers:
        try:
            decimals = int(tx.get("tokenDecimal", 18))
            value = int(tx.get("value", 0)) / (10 ** decimals)
            if value >= min_tokens:
                tx_ts = int(tx.get("timeStamp", 0))
                whale_transfers.append({
                    "hash": tx.get("hash", ""),
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value": round(value, 2),
                    "timestamp": datetime.utcfromtimestamp(tx_ts).strftime("%Y-%m-%d %H:%M"),
                })
        except (ValueError, TypeError):
            continue

    whale_transfers.sort(key=lambda x: x["value"], reverse=True)
    return whale_transfers[:limit]


def get_whale_accumulation_indicator(contract_address, chain, days=7):
    """
    Identify top 20 addresses by volume and classify accumulation behavior.

    Returns:
        {
            "top_addresses": [{"address": ..., "total_in": ..., "total_out": ..., "net_flow": ..., "status": ...}],
            "accumulating_count": int,
            "distributing_count": int,
            "neutral_count": int,
            "score": float  # -1.0 (all distributing) to +1.0 (all accumulating)
        }
    """
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    start_ts = int(start.timestamp())
    end_ts = int(now.timestamp())

    transfers = _fetch_token_transfers(contract_address, chain, start_ts, end_ts, max_pages=3)

    if isinstance(transfers, dict) and "error" in transfers:
        return transfers
    if not transfers:
        return {
            "top_addresses": [],
            "accumulating_count": 0,
            "distributing_count": 0,
            "neutral_count": 0,
            "score": 0.0,
        }

    # Track inflows and outflows per address
    address_flows = defaultdict(lambda: {"total_in": 0.0, "total_out": 0.0})

    for tx in transfers:
        try:
            decimals = int(tx.get("tokenDecimal", 18))
            value = int(tx.get("value", 0)) / (10 ** decimals)
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()

            if to_addr:
                address_flows[to_addr]["total_in"] += value
            if from_addr:
                address_flows[from_addr]["total_out"] += value
        except (ValueError, TypeError):
            continue

    # Get top 20 by total volume
    address_list = []
    for addr, flows in address_flows.items():
        total_volume = flows["total_in"] + flows["total_out"]
        net_flow = flows["total_in"] - flows["total_out"]
        address_list.append({
            "address": addr,
            "total_in": round(flows["total_in"], 2),
            "total_out": round(flows["total_out"], 2),
            "net_flow": round(net_flow, 2),
            "total_volume": round(total_volume, 2),
        })

    address_list.sort(key=lambda x: x["total_volume"], reverse=True)
    top_addresses = address_list[:20]

    # Classify each address
    accumulating = 0
    distributing = 0
    neutral = 0

    for addr_data in top_addresses:
        net = addr_data["net_flow"]
        total_vol = addr_data["total_volume"]
        # Use 5% of volume as threshold for neutral
        threshold = total_vol * 0.05 if total_vol > 0 else 0

        if net > threshold:
            addr_data["status"] = "Accumulating"
            accumulating += 1
        elif net < -threshold:
            addr_data["status"] = "Distributing"
            distributing += 1
        else:
            addr_data["status"] = "Neutral"
            neutral += 1

    # Score: ranges from -1.0 (all distributing) to +1.0 (all accumulating)
    total_classified = accumulating + distributing + neutral
    if total_classified > 0:
        score = round((accumulating - distributing) / total_classified, 2)
    else:
        score = 0.0

    return {
        "top_addresses": top_addresses,
        "accumulating_count": accumulating,
        "distributing_count": distributing,
        "neutral_count": neutral,
        "score": score,
    }


def get_exchange_flow_analysis(contract_address, chain, days=7):
    """
    Analyze token flows to/from known exchange addresses.
    Inflow (to exchange) = potential selling pressure.
    Outflow (from exchange) = potential buying/accumulation.

    Returns:
        {
            "exchange_flows": {exchange_name: {"inflow": float, "outflow": float, "net_flow": float}},
            "daily_flows": [{"date": ..., "inflow": ..., "outflow": ..., "net_flow": ...}],
            "total_inflow": float,
            "total_outflow": float,
            "net_flow": float,
            "signal": str
        }
    """
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    start_ts = int(start.timestamp())
    end_ts = int(now.timestamp())

    transfers = _fetch_token_transfers(contract_address, chain, start_ts, end_ts, max_pages=3)

    if isinstance(transfers, dict) and "error" in transfers:
        return transfers
    if not transfers:
        return {
            "exchange_flows": {},
            "daily_flows": [],
            "total_inflow": 0,
            "total_outflow": 0,
            "net_flow": 0,
            "signal": "Neutral",
        }

    exchange_flows = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    daily_flows = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})

    for tx in transfers:
        try:
            decimals = int(tx.get("tokenDecimal", 18))
            value = int(tx.get("value", 0)) / (10 ** decimals)
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()
            tx_ts = int(tx.get("timeStamp", 0))
            date_str = datetime.utcfromtimestamp(tx_ts).strftime("%Y-%m-%d")

            # Inflow: tokens sent TO an exchange (selling pressure)
            to_exchange = _EXCHANGE_LOOKUP.get(to_addr)
            if to_exchange:
                exchange_flows[to_exchange]["inflow"] += value
                daily_flows[date_str]["inflow"] += value

            # Outflow: tokens sent FROM an exchange (buying/accumulation)
            from_exchange = _EXCHANGE_LOOKUP.get(from_addr)
            if from_exchange:
                exchange_flows[from_exchange]["outflow"] += value
                daily_flows[date_str]["outflow"] += value

        except (ValueError, TypeError):
            continue

    # Build exchange flow summary
    exchange_summary = {}
    for exchange_name, flows in exchange_flows.items():
        net = flows["outflow"] - flows["inflow"]
        exchange_summary[exchange_name] = {
            "inflow": round(flows["inflow"], 2),
            "outflow": round(flows["outflow"], 2),
            "net_flow": round(net, 2),
        }

    # Build daily flow list
    daily_flow_list = []
    for date_str in sorted(daily_flows.keys()):
        flows = daily_flows[date_str]
        net = flows["outflow"] - flows["inflow"]
        daily_flow_list.append({
            "date": date_str,
            "inflow": round(flows["inflow"], 2),
            "outflow": round(flows["outflow"], 2),
            "net_flow": round(net, 2),
        })

    total_inflow = sum(f["inflow"] for f in exchange_flows.values())
    total_outflow = sum(f["outflow"] for f in exchange_flows.values())
    net_flow = total_outflow - total_inflow

    # Signal interpretation
    if net_flow > 0:
        signal = "Bullish"
    elif net_flow < 0:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return {
        "exchange_flows": exchange_summary,
        "daily_flows": daily_flow_list,
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "net_flow": round(net_flow, 2),
        "signal": signal,
    }
