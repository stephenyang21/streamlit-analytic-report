import requests
import pandas as pd
from datetime import datetime

SYMBOL = "RLSUSDT"
BASE_URL_V1 = "https://fapi.binance.com/fapi/v1"
BASE_URL_DATA = "https://fapi.binance.com/futures/data"
TIMEOUT = 15


def get_ticker_24hr():
    """Get 24hr ticker statistics for RLSUSDT futures."""
    try:
        resp = requests.get(
            f"{BASE_URL_V1}/ticker/24hr",
            params={"symbol": SYMBOL},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if "code" in data:
            return {"error": data.get("msg", str(data))}
        return {
            "last_price": float(data.get("lastPrice", 0)),
            "price_change_pct": float(data.get("priceChangePercent", 0)),
            "high": float(data.get("highPrice", 0)),
            "low": float(data.get("lowPrice", 0)),
            "volume": float(data.get("volume", 0)),
            "quote_volume": float(data.get("quoteVolume", 0)),
            "trade_count": int(data.get("count", 0)),
            "weighted_avg_price": float(data.get("weightedAvgPrice", 0)),
        }
    except Exception as e:
        return {"error": str(e)}


def get_klines(interval="1d", limit=30):
    """Get candlestick/kline data for RLSUSDT futures."""
    try:
        resp = requests.get(
            f"{BASE_URL_V1}/klines",
            params={"symbol": SYMBOL, "interval": interval, "limit": limit},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, dict) and "code" in data:
            return {"error": data.get("msg", str(data))}

        rows = []
        for k in data:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(k[0] / 1000),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "quote_volume": float(k[7]),
                "trades": int(k[8]),
                "taker_buy_vol": float(k[9]),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return {"error": str(e)}


def get_funding_rate_history(limit=100):
    """Get funding rate history for RLSUSDT."""
    try:
        resp = requests.get(
            f"{BASE_URL_V1}/fundingRate",
            params={"symbol": SYMBOL, "limit": limit},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, dict) and "code" in data:
            return {"error": data.get("msg", str(data))}

        rows = []
        for entry in data:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(int(entry["fundingTime"]) / 1000),
                "funding_rate": float(entry.get("fundingRate", 0)),
                "mark_price": float(entry.get("markPrice", 0)),
            })

        if not rows:
            return {"error": "No funding rate data available"}

        df = pd.DataFrame(rows)
        return {
            "df": df,
            "current_rate": df.iloc[-1]["funding_rate"] if len(df) > 0 else 0,
            "avg_rate": df["funding_rate"].mean(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_open_interest():
    """Get current open interest snapshot for RLSUSDT."""
    try:
        resp = requests.get(
            f"{BASE_URL_V1}/openInterest",
            params={"symbol": SYMBOL},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if "code" in data:
            return {"error": data.get("msg", str(data))}
        return {
            "open_interest": float(data.get("openInterest", 0)),
        }
    except Exception as e:
        return {"error": str(e)}


def get_open_interest_history(period="1d", limit=30):
    """Get historical open interest for RLSUSDT."""
    try:
        resp = requests.get(
            f"{BASE_URL_DATA}/openInterestHist",
            params={"symbol": SYMBOL, "period": period, "limit": limit},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, dict) and "code" in data:
            return {"error": data.get("msg", str(data))}

        rows = []
        for entry in data:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(int(entry["timestamp"]) / 1000),
                "open_interest": float(entry.get("sumOpenInterest", 0)),
                "open_interest_value": float(entry.get("sumOpenInterestValue", 0)),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return {"error": str(e)}


def get_long_short_ratio(period="1d", limit=30):
    """Get top trader long/short position ratio for RLSUSDT."""
    try:
        resp = requests.get(
            f"{BASE_URL_DATA}/topLongShortPositionRatio",
            params={"symbol": SYMBOL, "period": period, "limit": limit},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, dict) and "code" in data:
            return {"error": data.get("msg", str(data))}

        rows = []
        for entry in data:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(int(entry["timestamp"]) / 1000),
                "long_account": float(entry.get("longAccount", 0)),
                "short_account": float(entry.get("shortAccount", 0)),
                "long_short_ratio": float(entry.get("longShortRatio", 1)),
            })

        if not rows:
            return {"error": "No long/short ratio data available"}

        df = pd.DataFrame(rows)
        latest_ratio = df.iloc[-1]["long_short_ratio"] if len(df) > 0 else 1.0
        signal = "Bullish" if latest_ratio > 1.0 else ("Bearish" if latest_ratio < 1.0 else "Neutral")
        return {
            "df": df,
            "latest_ratio": latest_ratio,
            "signal": signal,
        }
    except Exception as e:
        return {"error": str(e)}


def get_taker_buy_sell_ratio(period="1d", limit=30):
    """Get taker buy/sell volume ratio for RLSUSDT."""
    try:
        resp = requests.get(
            f"{BASE_URL_DATA}/takerlongshortRatio",
            params={"symbol": SYMBOL, "period": period, "limit": limit},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, dict) and "code" in data:
            return {"error": data.get("msg", str(data))}

        rows = []
        for entry in data:
            rows.append({
                "timestamp": datetime.utcfromtimestamp(int(entry["timestamp"]) / 1000),
                "buy_sell_ratio": float(entry.get("buySellRatio", 1)),
                "buy_vol": float(entry.get("buyVol", 0)),
                "sell_vol": float(entry.get("sellVol", 0)),
            })

        if not rows:
            return {"error": "No taker buy/sell data available"}

        df = pd.DataFrame(rows)
        latest_ratio = df.iloc[-1]["buy_sell_ratio"] if len(df) > 0 else 1.0
        signal = "Bullish" if latest_ratio > 1.0 else ("Bearish" if latest_ratio < 1.0 else "Neutral")
        return {
            "df": df,
            "latest_ratio": latest_ratio,
            "signal": signal,
        }
    except Exception as e:
        return {"error": str(e)}


def get_all_futures_data():
    """Fetch all futures data for RLSUSDT. Each key may independently contain 'error'."""
    return {
        "ticker": get_ticker_24hr(),
        "open_interest": get_open_interest(),
        "open_interest_history": get_open_interest_history(),
        "funding_rate": get_funding_rate_history(),
        "long_short_ratio": get_long_short_ratio(),
        "taker_buy_sell": get_taker_buy_sell_ratio(),
    }


def compute_market_signal(data):
    """
    Compute an overall market signal from futures data.

    Weights:
        Funding rate: 0.20
        Long/Short ratio: 0.25
        Taker buy/sell: 0.25
        OI trend: 0.15
        Price momentum: 0.15

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

    # 1. Funding rate (weight 0.20)
    funding = data.get("funding_rate", {})
    if not isinstance(funding, dict) or "error" not in funding:
        current_rate = funding.get("current_rate", 0)
        if current_rate > 0.0001:
            score = min(current_rate / 0.001, 1.0)
        elif current_rate < -0.0001:
            score = max(current_rate / 0.001, -1.0)
        else:
            score = 0.0
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Funding Rate",
            "value": f"{current_rate:.6f}",
            "signal": signal,
            "weight": 0.20,
            "score": round(score, 3),
        })
        total_score += score * 0.20
        total_weight += 0.20

    # 2. Long/Short ratio (weight 0.25)
    ls = data.get("long_short_ratio", {})
    if not isinstance(ls, dict) or "error" not in ls:
        ratio = ls.get("latest_ratio", 1.0)
        score = max(min((ratio - 1.0) / 0.5, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Long/Short Ratio",
            "value": f"{ratio:.4f}",
            "signal": signal,
            "weight": 0.25,
            "score": round(score, 3),
        })
        total_score += score * 0.25
        total_weight += 0.25

    # 3. Taker buy/sell ratio (weight 0.25)
    taker = data.get("taker_buy_sell", {})
    if not isinstance(taker, dict) or "error" not in taker:
        ratio = taker.get("latest_ratio", 1.0)
        score = max(min((ratio - 1.0) / 0.3, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Taker Buy/Sell",
            "value": f"{ratio:.4f}",
            "signal": signal,
            "weight": 0.25,
            "score": round(score, 3),
        })
        total_score += score * 0.25
        total_weight += 0.25

    # 4. OI trend (weight 0.15)
    oi_hist = data.get("open_interest_history", {})
    if isinstance(oi_hist, pd.DataFrame) and len(oi_hist) >= 2:
        recent = oi_hist["open_interest"].iloc[-1]
        older = oi_hist["open_interest"].iloc[0]
        if older > 0:
            change_pct = (recent - older) / older
            score = max(min(change_pct / 0.3, 1.0), -1.0)
        else:
            score = 0.0
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "OI Trend",
            "value": f"{change_pct * 100:.1f}%",
            "signal": signal,
            "weight": 0.15,
            "score": round(score, 3),
        })
        total_score += score * 0.15
        total_weight += 0.15

    # 5. Price momentum (weight 0.15)
    ticker = data.get("ticker", {})
    if not isinstance(ticker, dict) or "error" not in ticker:
        pct = ticker.get("price_change_pct", 0)
        score = max(min(pct / 10.0, 1.0), -1.0)
        signal = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        factors.append({
            "factor": "Price Momentum (24h)",
            "value": f"{pct:+.2f}%",
            "signal": signal,
            "weight": 0.15,
            "score": round(score, 3),
        })
        total_score += score * 0.15
        total_weight += 0.15

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
