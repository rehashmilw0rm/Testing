"""Paper portfolio: simulated fills and settlement against real resolutions."""

import json
import os
import time
from dataclasses import asdict, dataclass

from .markets import taker_fee_per_share


@dataclass
class Position:
    id: int
    slug: str
    question: str
    side: str       # up / down / both
    shares: float
    price: float    # per share (both: up ask + down ask)
    fees: float     # total fees paid
    cost: float     # total cash out
    opened_at: float
    ends_at: float
    kind: str
    fair: float
    status: str = "open"   # open / won / lost
    payout: float = 0.0
    settled_at: float = 0.0

    @property
    def pnl(self):
        return self.payout - self.cost if self.status != "open" else 0.0


class PaperBook:
    def __init__(self, path, starting_cash=100.0):
        self.path = path
        self.cash = starting_cash
        self.starting_cash = starting_cash
        self.positions = []
        self._next_id = 1
        if path and os.path.exists(path):
            self._load()

    def _load(self):
        with open(self.path) as f:
            data = json.load(f)
        self.cash = data["cash"]
        self.starting_cash = data["starting_cash"]
        self.positions = [Position(**p) for p in data["positions"]]
        self._next_id = max((p.id for p in self.positions), default=0) + 1

    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"cash": self.cash, "starting_cash": self.starting_cash,
                       "positions": [asdict(p) for p in self.positions]}, f, indent=1)
        os.replace(tmp, self.path)

    def spent_on(self, slug):
        return sum(p.cost for p in self.positions if p.slug == slug)

    def fill(self, signal, market, now=None):
        now = now or time.time()
        if signal.side == "both":
            ua, da = market.books["up"].best_ask[0], market.books["down"].best_ask[0]
            fee_ps = taker_fee_per_share(ua, market.fee_rate, market.fee_exponent) + \
                taker_fee_per_share(da, market.fee_rate, market.fee_exponent)
        else:
            fee_ps = taker_fee_per_share(signal.price, market.fee_rate, market.fee_exponent)
        fees = fee_ps * signal.shares
        cost = signal.price * signal.shares + fees
        if cost > self.cash:
            return None
        self.cash -= cost
        pos = Position(id=self._next_id, slug=market.slug, question=market.question, side=signal.side,
                       shares=signal.shares, price=signal.price, fees=round(fees, 6), cost=round(cost, 6),
                       opened_at=now, ends_at=market.end, kind=signal.kind, fair=signal.fair)
        self._next_id += 1
        self.positions.append(pos)
        self.save()
        return pos

    def settle(self, slug, winner, now=None):
        """winner is 'up' or 'down'. Returns positions that settled."""
        done = []
        for p in self.positions:
            if p.slug != slug or p.status != "open":
                continue
            won = p.side == "both" or p.side == winner
            p.payout = p.shares if won else 0.0
            p.status = "won" if won else "lost"
            p.settled_at = now or time.time()
            self.cash += p.payout
            done.append(p)
        if done:
            self.save()
        return done

    def open_slugs(self):
        return sorted({p.slug for p in self.positions if p.status == "open"})

    def summary(self):
        closed = [p for p in self.positions if p.status != "open"]
        wins = sum(1 for p in closed if p.status == "won")
        open_cost = sum(p.cost for p in self.positions if p.status == "open")
        realised = sum(p.pnl for p in closed)
        return {
            "cash": round(self.cash, 4),
            "starting_cash": self.starting_cash,
            "open_cost": round(open_cost, 4),
            "equity_at_cost": round(self.cash + open_cost, 4),
            "realised_pnl": round(realised, 4),
            "trades": len(self.positions),
            "settled": len(closed),
            "wins": wins,
            "win_rate": round(wins / len(closed), 4) if closed else None,
            "fees_paid": round(sum(p.fees for p in self.positions), 4),
        }
