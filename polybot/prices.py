"""Spot price feed from Binance public market data (no API key needed)."""

import math
import statistics

from .http import get_json

# data-api.binance.vision serves the same public market data as api.binance.com
# and is not geo-blocked in places where the main API is.
BASES = ["https://data-api.binance.vision", "https://api.binance.com"]


class BinanceFeed:
    def __init__(self, bases=None):
        self.bases = list(bases or BASES)

    def _get(self, path, params):
        err = None
        for base in self.bases:
            try:
                data = get_json(base + path, params)
                if isinstance(data, dict) and "code" in data and "msg" in data:
                    raise RuntimeError(data["msg"])
                return data
            except Exception as e:  # try the next mirror
                err = e
        raise RuntimeError(f"all Binance endpoints failed: {err}")

    def price(self, symbol):
        return float(self._get("/api/v3/ticker/price", {"symbol": symbol})["price"])

    def prices(self, symbols):
        data = self._get("/api/v3/ticker/price", {"symbols": "[" + ",".join(f'"{s}"' for s in symbols) + "]"})
        return {d["symbol"]: float(d["price"]) for d in data}

    def klines(self, symbol, interval, start_ms=None, end_ms=None, limit=1000):
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_ms is not None:
            params["startTime"] = int(start_ms)
        if end_ms is not None:
            params["endTime"] = int(end_ms)
        rows = self._get("/api/v3/klines", params)
        return [
            {"t": r[0] / 1000.0, "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
             "close": float(r[4]), "close_t": r[6] / 1000.0}
            for r in rows
        ]

    def volatility(self, symbol, minutes=120):
        """Realised volatility per sqrt(second), from 1m log returns."""
        rows = self.klines(symbol, "1m", limit=minutes + 1)
        return realised_vol([r["close"] for r in rows], 60.0)


def realised_vol(closes, step_seconds):
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    if len(rets) < 2:
        return 0.0
    return statistics.pstdev(rets) / math.sqrt(step_seconds)
