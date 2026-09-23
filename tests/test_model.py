import math
import unittest

from polybot.markets import Book, Market, slug_for, taker_fee_per_share, window_start
from polybot.model import fair_up
from polybot.paper import PaperBook
from polybot.strategy import Config, evaluate

SIGMA = 0.0001  # per sqrt(second), about 0.6% per hour


class ModelTests(unittest.TestCase):
    def test_at_the_money_is_coin_flip(self):
        for res in ("close", "twap"):
            self.assertAlmostEqual(fair_up(res, 100.0, 100.0, SIGMA, 600).p_up, 0.5, places=6)

    def test_monotonic_in_spot(self):
        lo = fair_up("twap", 100.0, 99.9, SIGMA, 300).p_up
        hi = fair_up("twap", 100.0, 100.1, SIGMA, 300).p_up
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_close_matches_lognormal_formula(self):
        p = fair_up("close", 100.0, 101.0, SIGMA, 900).p_up
        z = math.log(1.01) / (SIGMA * math.sqrt(900))
        self.assertAlmostEqual(p, 0.5 * (1 + math.erf(z / math.sqrt(2))), places=9)

    def test_twap_uncertainty_shrinks_inside_final_minute(self):
        wide = fair_up("twap", 100.0, 100.02, SIGMA, 120).sd
        narrow = fair_up("twap", 100.0, 100.02, SIGMA, 10, tail_avg=100.02).sd
        self.assertLess(narrow, wide)

    def test_twap_uses_observed_tail(self):
        # Spot is back at the strike, but the settlement average so far is well above it.
        p = fair_up("twap", 100.0, 100.0, SIGMA, 5, tail_avg=100.5).p_up
        self.assertGreater(p, 0.99)

    def test_expired_is_certain(self):
        self.assertEqual(fair_up("close", 100.0, 100.5, SIGMA, 0).p_up, 1.0)
        self.assertEqual(fair_up("close", 100.0, 99.5, SIGMA, 0).p_up, 0.0)

    def test_basis_noise_pulls_toward_half(self):
        sharp = fair_up("twap", 100.0, 100.01, SIGMA, 30, tail_avg=100.01).p_up
        fuzzy = fair_up("twap", 100.0, 100.01, SIGMA, 30, tail_avg=100.01, basis_sd=0.001).p_up
        self.assertLess(abs(fuzzy - 0.5), abs(sharp - 0.5))


class MarketTests(unittest.TestCase):
    def test_slugs(self):
        self.assertEqual(slug_for("btc", "15m", 1790192700), "btc-updown-15m-1790192700")
        # 19:00 UTC on 23 Sep 2026 is 3pm New York time (EDT)
        self.assertEqual(slug_for("btc", "1h", 1790190000), "bitcoin-up-or-down-september-23-2026-3pm-et")
        self.assertEqual(slug_for("xrp", "1h", 1790136000), "xrp-up-or-down-september-23-2026-12am-et")

    def test_window_start(self):
        self.assertEqual(window_start(1790192799, "15m"), 1790192700)
        self.assertEqual(window_start(1790192799, "4h"), 1790179200)

    def test_fee_peaks_at_half(self):
        f = lambda p: taker_fee_per_share(p, 0.07, 1)
        self.assertAlmostEqual(f(0.5), 0.5 * 0.07 * 0.25)
        self.assertGreater(f(0.5), f(0.2))
        self.assertEqual(f(1.0), 0.0)


def make_market(up_asks, down_asks, start=0.0, end=900.0):
    m = Market(asset="btc", timeframe="15m", slug="t", question="q", start=start, end=end, resolution="twap",
               up_token="u", down_token="d", fee_rate=0.07, fee_exponent=1, min_size=5)
    m.books = {"up": Book(bids=[], asks=up_asks), "down": Book(bids=[], asks=down_asks)}
    return m


class StrategyTests(unittest.TestCase):
    def test_no_trade_when_fairly_priced(self):
        m = make_market([(0.51, 500)], [(0.50, 500)])
        self.assertEqual(evaluate(m, 0.505, Config(), now=300), [])

    def test_value_trade_on_cheap_side(self):
        m = make_market([(0.40, 500)], [(0.62, 500)])
        sigs = evaluate(m, 0.55, Config(stake_usd=10), now=300)
        self.assertEqual([s.side for s in sigs], ["up"])
        self.assertAlmostEqual(sigs[0].shares, 25.0)
        self.assertGreater(sigs[0].edge, 0.1)

    def test_arb_when_both_sides_cheap(self):
        m = make_market([(0.45, 100)], [(0.45, 100)])
        kinds = {s.kind for s in evaluate(m, 0.5, Config(min_edge=1), now=300)}
        self.assertEqual(kinds, {"arb"})

    def test_respects_time_and_budget(self):
        m = make_market([(0.30, 500)], [(0.72, 500)])
        self.assertEqual(evaluate(m, 0.6, Config(), now=890), [])  # too close to expiry
        self.assertEqual(evaluate(m, 0.6, Config(max_position_usd=10), now=300, spent_usd=10), [])

    def test_confidence_is_capped(self):
        m = make_market([(0.98, 500)], [(0.03, 500)])
        # Model says 99.9% up, but capping at 97% means a 98c ask is not a buy.
        self.assertEqual([s for s in evaluate(m, 0.999, Config(), now=300) if s.side == "up"], [])


class PaperTests(unittest.TestCase):
    def test_fill_and_settle(self):
        book = PaperBook(None, starting_cash=100)
        m = make_market([(0.40, 500)], [(0.62, 500)])
        sig = evaluate(m, 0.55, Config(stake_usd=10), now=300)[0]
        pos = book.fill(sig, m, now=300)
        self.assertAlmostEqual(book.cash, 100 - pos.cost)
        book.settle("t", "up", now=1000)
        self.assertEqual(pos.status, "won")
        self.assertAlmostEqual(book.cash, 100 - pos.cost + 25)
        self.assertAlmostEqual(book.summary()["realised_pnl"], 25 - pos.cost, places=4)


if __name__ == "__main__":
    unittest.main()
