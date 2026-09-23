"""Turn fair values and order books into trade signals."""

from dataclasses import dataclass

from .markets import taker_fee_per_share


@dataclass
class Config:
    min_edge: float = 0.04          # required fair - (ask + fee), per $1 share
    max_confidence: float = 0.97    # never trust the model beyond this
    min_price: float = 0.03         # ignore dust quotes at the extremes
    max_price: float = 0.97
    min_seconds_left: float = 20.0  # too late: oracle/latency risk dominates
    min_elapsed_frac: float = 0.0   # wait until this fraction of the window has passed
    stake_usd: float = 10.0         # dollars per trade
    max_position_usd: float = 30.0  # per market
    arb_min_profit: float = 0.005   # per share, for buy-both-sides arb


@dataclass
class Signal:
    market_slug: str
    side: str          # "up" / "down" / "both"
    price: float       # limit price (both: combined cost)
    shares: float
    fair: float
    edge: float        # per share, after fees
    kind: str          # "value" or "arb"
    reason: str


def _clamp(p, lo, hi):
    return max(lo, min(hi, p))


def evaluate(market, p_up, cfg, now, spent_usd=0.0):
    """Return a list of Signals for one market (possibly empty)."""
    out = []
    remaining = market.end - now
    if not market.accepting_orders or remaining < cfg.min_seconds_left:
        return out
    if (now - market.start) / market.length < cfg.min_elapsed_frac:
        return out
    up_book, down_book = market.books.get("up"), market.books.get("down")
    if up_book is None or down_book is None:
        return out

    budget = max(0.0, cfg.max_position_usd - spent_usd)
    fee = lambda p: taker_fee_per_share(p, market.fee_rate, market.fee_exponent)

    # 1) Structural arbitrage: Up + Down always pays exactly $1.
    (ua, us), (da, ds) = up_book.best_ask, down_book.best_ask
    if ua is not None and da is not None:
        cost = ua + da + fee(ua) + fee(da)
        profit = 1.0 - cost
        if profit >= cfg.arb_min_profit:
            shares = min(us, ds, min(cfg.stake_usd, budget) / cost)
            if shares >= market.min_size:
                out.append(Signal(market.slug, "both", ua + da, round(shares, 2), 1.0, profit, "arb",
                                  f"up {ua:.3f} + down {da:.3f} + fees = {cost:.4f} < 1"))

    # 2) Value: model probability vs the price we can actually buy at.
    p_up = _clamp(p_up, 1 - cfg.max_confidence, cfg.max_confidence)
    for side, fair, (ask, size) in (("up", p_up, up_book.best_ask), ("down", 1 - p_up, down_book.best_ask)):
        if ask is None or not (cfg.min_price <= ask <= cfg.max_price):
            continue
        edge = fair - ask - fee(ask)
        if edge < cfg.min_edge:
            continue
        shares = min(size, min(cfg.stake_usd, budget) / ask)
        if shares < market.min_size:
            continue
        out.append(Signal(market.slug, side, ask, round(shares, 2), fair, edge, "value",
                          f"fair {fair:.3f} vs ask {ask:.3f} (fee {fee(ask):.4f})"))
    return out
