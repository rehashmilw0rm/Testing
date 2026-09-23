"""Fair-value model for Up/Down markets.

Price is modelled as driftless Brownian motion with volatility `sigma`
(per sqrt(second), in log terms). Two settlement rules exist on Polymarket:

* "close": Up if the price at `end` >= price at `start` (the hourly markets,
  settled on the Binance 1h candle).

      P(Up) = Phi(ln(S/K) / (sigma * sqrt(r)))

* "twap": the 5m / 15m / 4h markets. Their text says "TWAP of the time range",
  but the source is Chainlink's rolling 60-second TWAP stream, and checking
  resolved markets against Binance 1s data shows the rule is

      Up  iff  TWAP60(end) >= TWAP60(start)

  where TWAP60(t) is the average price over [t - 60s, t]. (A full-window
  average matched noticeably fewer resolutions; see `polybot verify`.)

  With r seconds left and window W = 60:
    r >= W: the settlement average is still entirely in the future:
        mean = S,  var = S^2 sigma^2 ((r - W) + W/3)
    r <  W: (W - r) seconds of it are already known with average A:
        mean = ((W - r) A + r S) / W,  sd = (r / W) S sigma sqrt(r / 3)

`basis_sd` (fractional price noise) covers the gap between our Binance feed
and the Chainlink oracle that actually settles the TWAP markets.
"""

import math
from dataclasses import dataclass

TWAP_WINDOW = 60.0


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@dataclass
class Estimate:
    p_up: float
    mean: float  # expected settlement value
    sd: float
    strike: float


def fair_up(resolution, strike, spot, sigma, remaining, tail_avg=None, basis_sd=0.0, window=TWAP_WINDOW):
    """Probability that the market resolves Up.

    tail_avg: for "twap" markets inside the final `window` seconds, the average
    price observed so far in [end - window, now].
    """
    if strike <= 0 or spot <= 0:
        raise ValueError("prices must be positive")
    r = max(0.0, remaining)

    if resolution == "close":
        mean = spot
        sd = spot * sigma * math.sqrt(r)
    elif resolution == "twap":
        if r >= window:
            mean = spot
            sd = spot * sigma * math.sqrt((r - window) + window / 3.0)
        else:
            known = window - r
            avg = spot if tail_avg is None else tail_avg
            mean = (known * avg + r * spot) / window
            sd = (r / window) * spot * sigma * math.sqrt(r / 3.0)
    else:
        raise ValueError(f"unknown resolution {resolution!r}")

    sd = math.hypot(sd, basis_sd * spot)
    if sd <= 0:
        p = 1.0 if mean >= strike else 0.0
    else:
        p = norm_cdf(math.log(mean / strike) / (sd / spot))
    return Estimate(p_up=p, mean=mean, sd=sd, strike=strike)
