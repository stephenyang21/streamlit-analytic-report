import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://api.kraken.com/0/public"
TIMEOUT = 15

# Tokens tracked on Kraken (name -> Kraken pair)
KRAKEN_PAIRS = {
    "Rayls": "RLSUSD",
    "zkSync Era": "ZKUSD",
    "Plume": "PLUMEUSD",
    "Avalanche": "AVAXUSD",
    "Ondo Finance": "ONDOUSD",
    "Polygon": "POLUSD",
    "Chainlink": "LINKUSD",
}

# Kraken OHLC interval mapping (in minutes)
INTERVAL_MAP = {
    "1d": 1440,
    "4h": 240,
    "1h": 60,
    "30m": 30,
    "15m": 15,
}


def _get_pair_key(result):
    """Extract the actual pair key from Kraken result (ignores 'last')."""
    keys = [k for k in result.keys() if k != "last"]
    return keys[0] if keys else None


def get_ticker(pair="RLSUSD"):
    """Get 24hr ticker statistics for a pair from Kraken."""
    try:
        resp = requests.get(
            f"{BASE_URL}/Ticker",
            params={"pair": pair},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error"):
            return {"error": ", ".join(data["error"])}

        result = data["result"]
        pair_key = list(result.keys())[0]
        t = result[pair_key]

        last_price = float(t["c"][0])
        open_price = float(t["o"])
        price_change_pct = ((last_price - open_price) / open_price * 100) if open_price else 0

        return {
            "last_price": last_price,
            "open_price": open_price,
            "price_change_pct": round(price_change_pct, 2),
            "high": float(t["h"][1]),       # 24h high
            "low": float(t["l"][1]),        # 24h low
            "volume": float(t["v"][1]),     # 24h volume
            "vwap": float(t["p"][1]),       # 24h VWAP
            "trade_count": int(t["t"][1]),  # 24h trades
            "ask": float(t["a"][0]),
            "bid": float(t["b"][0]),
            "spread": round(float(t["a"][0]) - float(t["b"][0]), 8),
        }
    except Exception as e:
        return {"error": str(e)}


def get_ohlc(pair="RLSUSD", interval="1d", limit=60):
    """Get OHLC candlestick data for a pair from Kraken."""
    try:
        kraken_interval = INTERVAL_MAP.get(interval, 1440)
        resp = requests.get(
            f"{BASE_URL}/OHLC",
            params={"pair": pair, "interval": kraken_interval},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error"):
            return {"error": ", ".join(data["error"])}

        result = data["result"]
        pair_key = _get_pair_key(result)
        if not pair_key:
            return {"error": "No data in response"}
        raw = result[pair_key]

        rows = []
        for candle in raw:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(candle[0]),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "vwap": float(candle[5]),
                "volume": float(candle[6]),
                "trades": int(candle[7]),
            })

        df = pd.DataFrame(rows)
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)
        return df
    except Exception as e:
        return {"error": str(e)}


def get_order_book(pair="RLSUSD", count=20):
    """Get order book depth for a pair from Kraken."""
    try:
        resp = requests.get(
            f"{BASE_URL}/Depth",
            params={"pair": pair, "count": count},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error"):
            return {"error": ", ".join(data["error"])}

        result = data["result"]
        pair_key = list(result.keys())[0]
        book = result[pair_key]

        asks = [{"price": float(a[0]), "volume": float(a[1]), "side": "Ask"} for a in book["asks"]]
        bids = [{"price": float(b[0]), "volume": float(b[1]), "side": "Bid"} for b in book["bids"]]

        total_ask_vol = sum(a["volume"] for a in asks)
        total_bid_vol = sum(b["volume"] for b in bids)
        total = total_ask_vol + total_bid_vol

        bid_pct = (total_bid_vol / total * 100) if total else 50
        ask_pct = (total_ask_vol / total * 100) if total else 50

        if total_bid_vol > 0:
            bid_ask_ratio = total_bid_vol / total_ask_vol if total_ask_vol else float("inf")
        else:
            bid_ask_ratio = 0

        return {
            "asks": asks,
            "bids": bids,
            "total_ask_volume": total_ask_vol,
            "total_bid_volume": total_bid_vol,
            "bid_pct": round(bid_pct, 1),
            "ask_pct": round(ask_pct, 1),
            "bid_ask_ratio": round(bid_ask_ratio, 4),
        }
    except Exception as e:
        return {"error": str(e)}


def get_recent_trades(pair="RLSUSD"):
    """Get recent trades for a pair from Kraken and compute buy/sell breakdown."""
    try:
        resp = requests.get(
            f"{BASE_URL}/Trades",
            params={"pair": pair},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error"):
            return {"error": ", ".join(data["error"])}

        result = data["result"]
        pair_key = _get_pair_key(result)
        if not pair_key:
            return {"error": "No data in response"}
        raw = result[pair_key]

        rows = []
        for trade in raw:
            rows.append({
                "price": float(trade[0]),
                "volume": float(trade[1]),
                "timestamp": datetime.utcfromtimestamp(trade[2]),
                "side": "buy" if trade[3] == "b" else "sell",
                "type": "limit" if trade[4] == "l" else "market",
            })

        df = pd.DataFrame(rows)
        if df.empty:
            return {"error": "No trade data available"}

        buy_vol = df.loc[df["side"] == "buy", "volume"].sum()
        sell_vol = df.loc[df["side"] == "sell", "volume"].sum()
        total_vol = buy_vol + sell_vol
        buy_count = (df["side"] == "buy").sum()
        sell_count = (df["side"] == "sell").sum()

        buy_sell_ratio = (buy_vol / sell_vol) if sell_vol > 0 else float("inf")

        return {
            "df": df,
            "buy_volume": buy_vol,
            "sell_volume": sell_vol,
            "total_volume": total_vol,
            "buy_count": int(buy_count),
            "sell_count": int(sell_count),
            "buy_sell_ratio": round(buy_sell_ratio, 4),
            "buy_pct": round(buy_vol / total_vol * 100, 1) if total_vol else 50,
        }
    except Exception as e:
        return {"error": str(e)}


def get_spread_history(pair="RLSUSD"):
    """Get recent spread history for a pair from Kraken."""
    try:
        resp = requests.get(
            f"{BASE_URL}/Spread",
            params={"pair": pair},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("error"):
            return {"error": ", ".join(data["error"])}

        result = data["result"]
        pair_key = _get_pair_key(result)
        if not pair_key:
            return {"error": "No data in response"}
        raw = result[pair_key]

        rows = []
        for entry in raw:
            bid = float(entry[1])
            ask = float(entry[2])
            mid = (bid + ask) / 2
            spread_bps = ((ask - bid) / mid * 10000) if mid else 0
            rows.append({
                "timestamp": datetime.utcfromtimestamp(entry[0]),
                "bid": bid,
                "ask": ask,
                "spread": round(ask - bid, 8),
                "spread_bps": round(spread_bps, 2),
            })

        df = pd.DataFrame(rows)
        return {
            "df": df,
            "avg_spread_bps": round(df["spread_bps"].mean(), 2) if not df.empty else 0,
            "current_spread_bps": df["spread_bps"].iloc[-1] if not df.empty else 0,
        }
    except Exception as e:
        return {"error": str(e)}


def get_all_market_data(pair="RLSUSD"):
    """Fetch all Kraken market data for a pair. Each key may independently contain 'error'."""
    return {
        "ticker": get_ticker(pair),
        "order_book": get_order_book(pair, count=25),
        "trades": get_recent_trades(pair),
        "spread": get_spread_history(pair),
    }


def get_all_tickers():
    """
    Fetch ticker data for all tracked tokens.
    Returns dict of {token_name: ticker_data} for tokens that are available.
    Tokens that return errors are skipped.
    """
    results = {}
    for name, pair in KRAKEN_PAIRS.items():
        ticker = get_ticker(pair)
        if isinstance(ticker, dict) and "error" not in ticker:
            ticker["pair"] = pair
            ticker["name"] = name
            results[name] = ticker
    return results


def get_peer_comparison():
    """
    Fetch comparison data (ticker + order book) for all tracked tokens.
    Returns dict of {token_name: {ticker, order_book}} for available tokens.
    """
    results = {}
    for name, pair in KRAKEN_PAIRS.items():
        ticker = get_ticker(pair)
        if isinstance(ticker, dict) and "error" in ticker:
            continue
        book = get_order_book(pair, count=15)
        trades = get_recent_trades(pair)
        results[name] = {
            "pair": pair,
            "ticker": ticker,
            "order_book": book if isinstance(book, dict) and "error" not in book else None,
            "trades": trades if isinstance(trades, dict) and "error" not in trades else None,
        }
    return results


def compute_market_signal(data):
    """
    Compute an overall market signal from Kraken spot market data.

    Weights:
        Price momentum (24h): 0.25
        Buy/Sell ratio (trades): 0.30
        Order book imbalance: 0.25
        Spread health: 0.20

    Returns:
        {
            "overall_signal": "Bullish" | "Bearish" | "Neutral",
            "signal_score": float (-1.0 to +1.0),
            "factors": [{"factor": str, "value": str, "signal": str, "weight": float, "score": float}]
        }
    """
    factors = []
    total_score = 0.0
    total_weight = 0.0

    # 1. Price momentum (weight 0.25)
    ticker = data.get("ticker", {})
    if isinstance(ticker, dict) and "error" not in ticker:
        pct = ticker.get("price_change_pct", 0)
        score = max(min(pct / 10.0, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Price Momentum (24h)",
            "value": f"{pct:+.2f}%",
            "signal": signal,
            "weight": 0.25,
            "score": round(score, 3),
        })
        total_score += score * 0.25
        total_weight += 0.25

    # 2. Buy/Sell volume ratio from trades (weight 0.30)
    trades = data.get("trades", {})
    if isinstance(trades, dict) and "error" not in trades:
        ratio = trades.get("buy_sell_ratio", 1.0)
        buy_pct = trades.get("buy_pct", 50)
        score = max(min((ratio - 1.0) / 0.5, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Buy/Sell Volume Ratio",
            "value": f"{ratio:.4f} ({buy_pct:.0f}% buys)",
            "signal": signal,
            "weight": 0.30,
            "score": round(score, 3),
        })
        total_score += score * 0.30
        total_weight += 0.30

    # 3. Order book imbalance (weight 0.25)
    book = data.get("order_book", {})
    if isinstance(book, dict) and "error" not in book:
        bid_ask_ratio = book.get("bid_ask_ratio", 1.0)
        bid_pct = book.get("bid_pct", 50)
        score = max(min((bid_ask_ratio - 1.0) / 1.0, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Order Book Imbalance",
            "value": f"{bid_ask_ratio:.4f} ({bid_pct:.0f}% bid vol)",
            "signal": signal,
            "weight": 0.25,
            "score": round(score, 3),
        })
        total_score += score * 0.25
        total_weight += 0.25

    # 4. Spread health (weight 0.20) - tighter spread = healthier market
    spread = data.get("spread", {})
    if isinstance(spread, dict) and "error" not in spread:
        avg_bps = spread.get("avg_spread_bps", 0)
        if avg_bps <= 20:
            score = 1.0
        elif avg_bps >= 100:
            score = -1.0
        else:
            score = 1.0 - (avg_bps - 20) / 40
            score = max(min(score, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Spread Health",
            "value": f"{avg_bps:.1f} bps avg",
            "signal": signal,
            "weight": 0.20,
            "score": round(score, 3),
        })
        total_score += score * 0.20
        total_weight += 0.20

    # Normalize
    if total_weight > 0:
        normalized_score = total_score / total_weight
    else:
        normalized_score = 0.0

    normalized_score = max(min(normalized_score, 1.0), -1.0)

    if normalized_score > 0.15:
        overall = "Bullish"
    elif normalized_score < -0.15:
        overall = "Bearish"
    else:
        overall = "Neutral"

    return {
        "overall_signal": overall,
        "signal_score": round(normalized_score, 3),
        "factors": factors,
    }
