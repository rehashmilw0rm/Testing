"""Offline checks against resolved markets.

verify:   does our reading of the settlement rule match real resolutions?
backtest: would the strategy have made money against historical market prices?
"""

import time

from . import markets as mk
from .http import get_json
from .model import TWAP_WINDOW, fair_up
from .prices import BinanceFeed, realised_vol
from .markets import taker_fee_per_share


def _past_markets(asset, timeframe, count, now):
    size = mk.TIMEFRAMES[timeframe]
    first = mk.window_start(now, timeframe) - 2 * size  # skip windows that may not be settled yet
    for i in range(count):
        start = first - i * size
        try:
            m = mk.fetch_market(asset, timeframe, start)
        except Exception:
            m = None
        if m and m.winner():
            yield m


def _second_prices(feed, symbol, t0, t1):
    """{unix second: close} from Binance 1s candles over [t0, t1)."""
    out = {}
    t = int(t0)
    while t < t1:
        rows = feed.klines(symbol, "1s", start_ms=t * 1000, end_ms=int(t1) * 1000 - 1, limit=1000)
        if not rows:
            break
        for r in rows:
            out[int(r["t"])] = r["close"]
        t = int(rows[-1]["t"]) + 1
    return out


def _std_error(xs):
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    return (var * len(xs)) ** 0.5


def _avg(px, t0, t1):
    vals = [px[t] for t in range(int(t0), int(t1)) if t in px]
    return sum(vals) / len(vals) if vals else None


def verify(asset="btc", timeframe="5m", count=30, feed=None, now=None):
    """Compare candidate settlement rules with how markets actually resolved."""
    feed = feed or BinanceFeed()
    now = now or time.time()
    tally = {"twap60 (end vs start)": 0, "close vs open": 0, "full-window average vs open": 0}
    n = 0
    for m in _past_markets(asset, timeframe, count, now):
        px = _second_prices(feed, m.symbol, m.start - TWAP_WINDOW, m.end)
        if m.start not in px or not px:
            continue
        open_ = feed.klines(m.symbol, "1s", start_ms=m.start * 1000, limit=1)[0]["open"]
        close = px[max(px)]
        rules = {
            "twap60 (end vs start)": _avg(px, m.end - TWAP_WINDOW, m.end) >= _avg(px, m.start - TWAP_WINDOW, m.start),
            "close vs open": close >= open_,
            "full-window average vs open": _avg(px, m.start, m.end) >= open_,
        }
        n += 1
        for name, up in rules.items():
            tally[name] += (("up" if up else "down") == m.winner())
    return n, tally


def load_windows(asset="btc", timeframe="15m", count=40, feed=None, now=None, progress=None):
    """Download everything needed to replay resolved markets (done once, reused by sweeps)."""
    feed = feed or BinanceFeed()
    now = now or time.time()
    out = []
    for m in _past_markets(asset, timeframe, count, now):
        try:
            out.append(_load_window(m, feed))
        except Exception as e:  # one bad window shouldn't sink the run
            if progress:
                progress(f"{m.slug} skipped ({e})")
            continue
        if out[-1] is None:
            out.pop()
        elif progress:
            progress(m.slug)
    return out


def _load_window(m, feed):
    hist = get_json(f"{mk.CLOB}/prices-history",
                    {"market": m.up_token, "startTs": int(m.start), "endTs": int(m.end), "fidelity": 1})
    hist = [(int(h["t"]), float(h["p"])) for h in hist.get("history", [])]
    if not hist:
        return None
    px = _second_prices(feed, m.symbol, m.start - TWAP_WINDOW, m.end)
    vol_rows = feed.klines(m.symbol, "1m", end_ms=m.start * 1000, limit=121)
    strike = _avg(px, m.start - TWAP_WINDOW, m.start) if m.resolution == "twap" else \
        feed.klines(m.symbol, "1h", start_ms=m.start * 1000, limit=1)[0]["open"]
    if strike is None:
        return None
    return {"market": m, "hist": hist, "px": px, "strike": strike,
            "sigma": realised_vol([r["close"] for r in vol_rows], 60.0),
            "outcome": 1.0 if m.winner() == "up" else 0.0}


def replay(windows, min_edge=0.04, half_spread=0.01, vol_mult=1.0, basis_sd=0.0002, min_seconds_left=20,
           max_confidence=0.97):
    """Replay downloaded windows minute by minute against Polymarket's price history.

    Polymarket's price history is a mid/last price, not the ask we would pay, so
    `half_spread` is added to every simulated buy. Treat results as optimistic.
    """
    trades, brier_model, brier_market, points = [], 0.0, 0.0, 0
    for w in windows:
        m, px, outcome = w["market"], w["px"], w["outcome"]
        sigma = w["sigma"] * vol_mult
        traded = False
        for t, p_mkt in w["hist"]:
            remaining = m.end - t
            if not (m.start < t and remaining >= min_seconds_left) or t not in px:
                continue
            tail = _avg(px, m.end - TWAP_WINDOW, t) if m.resolution == "twap" and remaining < TWAP_WINDOW else None
            p = fair_up(m.resolution, w["strike"], px[t], sigma, remaining, tail, basis_sd).p_up
            p = min(max_confidence, max(1 - max_confidence, p))
            points += 1
            brier_model += (p - outcome) ** 2
            brier_market += (p_mkt - outcome) ** 2
            if traded:
                continue
            for side, fair, ask in (("up", p, p_mkt + half_spread), ("down", 1 - p, 1 - p_mkt + half_spread)):
                if not 0.03 <= ask <= 0.97:
                    continue
                fee = taker_fee_per_share(ask, m.fee_rate, m.fee_exponent)
                if fair - ask - fee >= min_edge:
                    won = (side == "up") == (outcome == 1.0)
                    trades.append({"slug": m.slug, "side": side, "t_left": remaining, "price": ask, "fair": fair,
                                   "fee": fee, "won": won, "pnl": (1.0 if won else 0.0) - ask - fee})
                    traded = True
                    break
    pnl = sum(t["pnl"] for t in trades)
    cost = sum(t["price"] + t["fee"] for t in trades)
    return {
        "windows": len(windows),
        "price_points": points,
        # Lower is better. If the model can't beat the market's own Brier score it has no edge.
        "brier_model": round(brier_model / points, 4) if points else None,
        "brier_market": round(brier_market / points, 4) if points else None,
        "trades": len(trades),
        "wins": sum(t["won"] for t in trades),
        "pnl_per_share_total": round(pnl, 4),
        "roi": round(pnl / cost, 4) if cost else None,
        # One standard error of total P&L; a result inside +/- 2 of these is noise.
        "pnl_std_error": round(_std_error([t["pnl"] for t in trades]), 4),
        "detail": trades,
    }


def backtest(asset="btc", timeframe="15m", count=40, progress=None, **kw):
    return replay(load_windows(asset, timeframe, count, progress=progress), **kw)
