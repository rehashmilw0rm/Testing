"""Discover Polymarket crypto Up/Down markets and read their order books."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .http import get_json

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
ET = ZoneInfo("America/New_York")

ASSETS = {
    # asset: (Binance symbol, name used in hourly slugs)
    "btc": ("BTCUSDT", "bitcoin"),
    "eth": ("ETHUSDT", "ethereum"),
    "sol": ("SOLUSDT", "solana"),
    "xrp": ("XRPUSDT", "xrp"),
}

TIMEFRAMES = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400}


@dataclass
class Book:
    bids: list  # [(price, size)] best first
    asks: list  # [(price, size)] best first

    @property
    def best_bid(self):
        return self.bids[0] if self.bids else (None, 0.0)

    @property
    def best_ask(self):
        return self.asks[0] if self.asks else (None, 0.0)


@dataclass
class Market:
    asset: str
    timeframe: str
    slug: str
    question: str
    start: float  # unix seconds
    end: float
    resolution: str  # "twap" (Chainlink TWAP vs start price) or "close" (Binance candle close vs open)
    up_token: str
    down_token: str
    fee_rate: float = 0.0
    fee_exponent: float = 1.0
    min_size: float = 5.0
    tick: float = 0.01
    accepting_orders: bool = True
    closed: bool = False
    outcome_prices: tuple = ()
    books: dict = field(default_factory=dict)  # "up"/"down" -> Book

    @property
    def symbol(self):
        return ASSETS[self.asset][0]

    @property
    def length(self):
        return self.end - self.start

    def winner(self):
        """'up' / 'down' once Polymarket has resolved the market, else None."""
        if not self.closed or len(self.outcome_prices) != 2:
            return None
        up, down = self.outcome_prices
        if up >= 0.99:
            return "up"
        if down >= 0.99:
            return "down"
        return None


def taker_fee_per_share(price, rate, exponent):
    """Polymarket crypto taker fee, per share bought at `price`.

    Published formula: fee = shares * price * rate * (price * (1 - price)) ** exponent.
    """
    return price * rate * (price * (1 - price)) ** exponent


def window_start(ts, timeframe):
    if timeframe == "1h":
        return int(ts // 3600 * 3600)
    size = TIMEFRAMES[timeframe]
    return int(ts // size * size)


def slug_for(asset, timeframe, start):
    if timeframe == "1h":
        dt = datetime.fromtimestamp(start, tz=timezone.utc).astimezone(ET)
        hour = dt.hour % 12 or 12
        ampm = "am" if dt.hour < 12 else "pm"
        month = dt.strftime("%B").lower()
        return f"{ASSETS[asset][1]}-up-or-down-{month}-{dt.day}-{dt.year}-{hour}{ampm}-et"
    return f"{asset}-updown-{timeframe}-{start}"


def _iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def parse_market(asset, timeframe, event):
    m = event["markets"][0]
    outcomes = json.loads(m.get("outcomes") or "[]")
    tokens = json.loads(m.get("clobTokenIds") or "[]")
    if len(tokens) != 2 or [o.lower() for o in outcomes] != ["up", "down"]:
        return None
    start = _iso(m.get("eventStartTime") or event.get("startTime"))
    end = _iso(m["endDate"])
    desc = (m.get("description") or "").lower()
    resolution = "twap" if "twap" in desc else "close"
    sched = m.get("feeSchedule") or {}
    fees_on = bool(m.get("feesEnabled"))
    prices = tuple(float(p) for p in json.loads(m.get("outcomePrices") or "[]"))
    return Market(
        asset=asset,
        timeframe=timeframe,
        slug=event["slug"],
        question=m.get("question", event.get("title", "")),
        start=start,
        end=end,
        resolution=resolution,
        up_token=tokens[0],
        down_token=tokens[1],
        fee_rate=float(sched.get("rate", 0.0)) if fees_on else 0.0,
        fee_exponent=float(sched.get("exponent", 1.0)),
        min_size=float(m.get("orderMinSize") or 5),
        tick=float(m.get("orderPriceMinTickSize") or 0.01),
        accepting_orders=bool(m.get("acceptingOrders", True)),
        closed=bool(m.get("closed")),
        outcome_prices=prices,
    )


def fetch_market(asset, timeframe, start):
    slug = slug_for(asset, timeframe, start)
    events = get_json(f"{GAMMA}/events", {"slug": slug})
    if not events or not events[0].get("markets"):
        return None
    return parse_market(asset, timeframe, events[0])


def fetch_by_slug(slug):
    events = get_json(f"{GAMMA}/events", {"slug": slug})
    if not events or not events[0].get("markets"):
        return None
    for asset in ASSETS:
        for tf in TIMEFRAMES:
            if slug.startswith(f"{asset}-updown-{tf}-") or (tf == "1h" and slug.startswith(ASSETS[asset][1] + "-up-or-down-")):
                return parse_market(asset, tf, events[0])
    return None


def discover(assets, timeframes, now, pool=None):
    """Return the currently running market for each asset/timeframe pair."""
    jobs = [(a, tf, window_start(now, tf)) for a in assets for tf in timeframes]
    own = pool is None
    pool = pool or ThreadPoolExecutor(max_workers=16)
    try:
        results = list(pool.map(lambda j: _safe(fetch_market, *j), jobs))
    finally:
        if own:
            pool.shutdown()
    return [m for m in results if m is not None and m.start <= now < m.end]


def fetch_book(token_id):
    data = get_json(f"{CLOB}/book", {"token_id": token_id})
    bids = sorted(((float(b["price"]), float(b["size"])) for b in data.get("bids", [])), reverse=True)
    asks = sorted((float(a["price"]), float(a["size"])) for a in data.get("asks", []))
    return Book(bids=bids, asks=asks)


def load_books(markets, pool=None):
    jobs = [(m, side, tok) for m in markets for side, tok in (("up", m.up_token), ("down", m.down_token))]
    own = pool is None
    pool = pool or ThreadPoolExecutor(max_workers=16)
    try:
        books = list(pool.map(lambda j: _safe(fetch_book, j[2]), jobs))
    finally:
        if own:
            pool.shutdown()
    for (m, side, _), book in zip(jobs, books):
        if book is not None:
            m.books[side] = book


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None
