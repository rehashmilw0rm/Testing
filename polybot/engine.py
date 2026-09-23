"""Main loop: discover markets, price them, paper-trade the mispricings."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor

from . import markets as mk
from .model import TWAP_WINDOW, fair_up
from .paper import PaperBook
from .prices import BinanceFeed
from .strategy import Config, evaluate

log = logging.getLogger("polybot")


class Engine:
    def __init__(self, assets, timeframes, cfg=None, book_path="state/paper.json", starting_cash=100.0,
                 vol_mult=1.0, basis_sd=0.0002, feed=None):
        self.assets = assets
        self.timeframes = timeframes
        self.cfg = cfg or Config()
        self.feed = feed or BinanceFeed()
        self.book = PaperBook(book_path, starting_cash)
        self.vol_mult = vol_mult
        self.basis_sd = basis_sd
        self.pool = ThreadPoolExecutor(max_workers=16)
        self.markets = {}      # slug -> Market
        self.strikes = {}      # slug -> strike price
        self.vols = {}         # symbol -> (sigma, fetched_at)
        self.rows = []         # latest per-market view, for the dashboard
        self.events = []       # recent fills / settlements
        self.last_discovery = 0.0
        self.last_error = None
        self.cycles = 0

    # ---- data -------------------------------------------------------------

    def _refresh_markets(self, now):
        stale = any(m.end <= now for m in self.markets.values())
        if not self.markets or stale or now - self.last_discovery > 60:
            found = mk.discover(self.assets, self.timeframes, now, self.pool)
            self.markets = {m.slug: m for m in found}
            self.last_discovery = now
            for slug in list(self.strikes):
                if slug not in self.markets:
                    del self.strikes[slug]

    def _sigma(self, symbol, now):
        cached = self.vols.get(symbol)
        if cached and now - cached[1] < 60:
            return cached[0]
        sigma = self.feed.volatility(symbol) * self.vol_mult
        self.vols[symbol] = (sigma, now)
        return sigma

    def _window_stats(self, m, now):
        """Strike and, for TWAP markets in their last minute, the settlement average so far."""
        if m.slug not in self.strikes:
            if m.resolution == "close":
                k = self.feed.klines(m.symbol, "1h", start_ms=m.start * 1000, limit=1)
                self.strikes[m.slug] = k[0]["open"] if k else None
            else:
                self.strikes[m.slug] = self._avg(m.symbol, m.start - TWAP_WINDOW, m.start)
        tail = None
        if m.resolution == "twap" and m.end - now < TWAP_WINDOW:
            tail = self._avg(m.symbol, m.end - TWAP_WINDOW, now)
        return self.strikes[m.slug], tail

    def _avg(self, symbol, t0, t1):
        rows = self.feed.klines(symbol, "1s", start_ms=t0 * 1000, end_ms=t1 * 1000 - 1, limit=1000)
        return sum(r["close"] for r in rows) / len(rows) if rows else None

    # ---- loop -------------------------------------------------------------

    def step(self, now=None):
        now = now or time.time()
        self.cycles += 1
        self._settle(now)
        self._refresh_markets(now)
        live = [m for m in self.markets.values() if m.start <= now < m.end]
        mk.load_books(live, self.pool)
        symbols = sorted({m.symbol for m in live})
        spots = self.feed.prices(symbols) if symbols else {}

        rows = []
        for m in sorted(live, key=lambda m: (m.asset, m.length)):
            row = {"slug": m.slug, "asset": m.asset.upper(), "timeframe": m.timeframe, "question": m.question,
                   "resolution": m.resolution, "ends_in": round(m.end - now, 1), "progress": (now - m.start) / m.length}
            try:
                spot = spots[m.symbol]
                strike, tail = self._window_stats(m, now)
                if strike is None:
                    continue
                est = fair_up(m.resolution, strike, spot, self._sigma(m.symbol, now),
                              remaining=m.end - now, tail_avg=tail, basis_sd=self.basis_sd)
                up, down = m.books.get("up"), m.books.get("down")
                row.update(spot=spot, strike=strike, fair_up=round(est.p_up, 4),
                           up_bid=up and up.best_bid[0], up_ask=up and up.best_ask[0],
                           down_bid=down and down.best_bid[0], down_ask=down and down.best_ask[0])
                if up and up.best_ask[0] is not None:
                    row["edge_up"] = round(est.p_up - up.best_ask[0], 4)
                if down and down.best_ask[0] is not None:
                    row["edge_down"] = round(1 - est.p_up - down.best_ask[0], 4)
                for sig in evaluate(m, est.p_up, self.cfg, now, self.book.spent_on(m.slug)):
                    if sig.kind == "arb" and not self._confirm_arb(m, est.p_up, now):
                        self._event(now, f"arb on {m.slug} vanished on re-check (stale book), skipped")
                        continue
                    pos = self.book.fill(sig, m, now)
                    if pos:
                        msg = (f"PAPER BUY {sig.side.upper()} {sig.shares} @ {sig.price:.3f} {m.slug} "
                               f"edge {sig.edge:+.3f} ({sig.reason})")
                        log.info(msg)
                        self._event(now, msg)
            except Exception as e:  # keep the loop alive; show the error
                row["error"] = str(e)
                log.warning("%s: %s", m.slug, e)
            rows.append(row)
        self.rows = rows

    def _confirm_arb(self, m, p_up, now):
        """Books for the two outcomes are read separately, so an apparent Up + Down < $1
        is often just two snapshots taken a moment apart. Re-read both and re-check."""
        mk.load_books([m], self.pool)
        return any(s.kind == "arb" for s in evaluate(m, p_up, self.cfg, now, self.book.spent_on(m.slug)))

    def _settle(self, now):
        for slug in self.book.open_slugs():
            pos = next(p for p in self.book.positions if p.slug == slug and p.status == "open")
            if now < pos.ends_at + 30:
                continue
            m = mk.fetch_by_slug(slug)
            winner = m and m.winner()
            if winner:
                for p in self.book.settle(slug, winner, now):
                    msg = f"SETTLED {slug}: {winner.upper()} won, {p.side} {p.status} pnl {p.pnl:+.2f}"
                    log.info(msg)
                    self._event(now, msg)

    def _event(self, now, msg):
        self.events.append({"t": now, "msg": msg})
        self.events = self.events[-200:]

    def state(self):
        return {
            "now": time.time(),
            "cycles": self.cycles,
            "config": vars(self.cfg),
            "markets": self.rows,
            "portfolio": self.book.summary(),
            "positions": [dict(vars(p), pnl=round(p.pnl, 4)) for p in self.book.positions[-100:]][::-1],
            "events": self.events[::-1][:50],
            "error": self.last_error,
        }

    def run(self, interval=5.0, stop=None):
        while not (stop and stop.is_set()):
            t0 = time.time()
            try:
                self.step()
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
                log.exception("cycle failed")
            time.sleep(max(0.0, interval - (time.time() - t0)))
