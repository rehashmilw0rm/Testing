# Polybot

A paper-trading bot for Polymarket's crypto "Up or Down" markets (BTC, ETH, SOL
and XRP over 5 minute, 15 minute, 1 hour and 4 hour windows). It's a working
version of the setup in the viral "$68 to $750K with Claude Code" posts: live
Binance prices, dozens of markets scanned at once, and a dashboard for a second
screen. It is honest about whether there's any money in it.

**It never places real orders.** Every trade is simulated against the live
order book and settled against Polymarket's real resolution.

## Quick start

Python 3.11+. Standard library only, so there's nothing to install.

```bash
python -m polybot scan                 # one snapshot: fair value vs order book for every market
python -m polybot run                  # paper-trade loop + dashboard on http://localhost:8765
python -m polybot verify               # check the settlement rule against resolved markets
python -m polybot backtest --sweep     # replay resolved markets against historical prices
python -m unittest discover -s tests   # unit tests
```

To use the dashboard on an iPad, open `http://<your computer's LAN IP>:8765`
on it.

Useful `run` flags: `--assets btc,eth`, `--timeframes 5m,15m`, `--min-edge 0.04`,
`--stake 10`, `--max-position 30`, `--cash 100`, `--interval 5`. The paper
portfolio is saved to `state/paper.json` and survives restarts.

## How it works

1. **Discover** (`markets.py`). Market slugs follow a pattern
   (`btc-updown-15m-<window start>`, `bitcoin-up-or-down-september-23-2026-3pm-et`),
   so the current market for each asset and timeframe is fetched directly from
   Polymarket's Gamma API. Order books come from the CLOB API.
2. **Price** (`model.py`). Fair probability of "Up" from the live Binance price,
   the strike and recent realised volatility, using Brownian motion.
3. **Decide** (`strategy.py`). Buy a side only when
   `fair - ask - taker fee >= min_edge`, capped by stake and per-market limits.
   It also checks the "Up ask + Down ask < $1" arbitrage and re-reads both books
   before acting on it, because the two books are fetched separately and a
   stale pair can look like free money.
4. **Paper-fill and settle** (`paper.py`). Fills at the best ask (including
   Polymarket's crypto taker fee, read from each market's fee schedule) and
   settles once Polymarket publishes the result.

### The settlement rule matters

The 5m, 15m and 4h markets say they resolve on "the TWAP of the time range",
but the source is Chainlink's *rolling 60-second* TWAP stream. The real rule is:

> Up if the 60s average ending at the window's close >= the 60s average ending at the window's open.

My first version read it as "average over the whole window vs open price", and
it showed 20 to 47 cent "edges" on every market. Those were fake. `polybot verify`
checks each reading against real resolutions:

| rule | BTC 5m (32 markets) | BTC 15m (20 markets) |
|---|---|---|
| 60s TWAP at end vs 60s TWAP at start | **32 / 32** | **20 / 20** |
| close vs open | 31 / 32 | 20 / 20 |
| full-window average vs open | 28 / 32 | 19 / 20 |

The hourly markets settle on the Binance 1h candle (close >= open), and the
model handles that case separately.

## Does it make money?

Probably not much, and nowhere near the numbers in the post. Backtest over
recent resolved markets (September 2026), using Polymarket's minute-by-minute
price history plus a 1 cent half-spread and the real fee:

| market | windows | model Brier | market Brier | trades | P&L per $1 share | 1 std error |
|---|---|---|---|---|---|---|
| BTC 15m | 96 | 0.1507 | 0.1521 | 88 | -4.21 | 4.49 |
| BTC 5m | 200 | 0.1552 | 0.1607 | 180 | +12.55 | 6.50 |

(vol multiplier 1.0, `min_edge` 0.04)

- **15m:** the model is no more accurate than the market price itself. P&L is
  noise at every volatility setting. No edge.
- **5m:** the model beats the market's mid price slightly, with P&L about 2
  standard errors above zero. That's worth watching, but it's not proof: the
  history is a 1-minute mid/last price, not the ask you'd actually pay, and a
  stale historical price flatters any strategy that reacts faster than it.
  The real test is a long `run` in paper mode against live asks.

Things the post leaves out:

- These markets are liquid and quoted by professional market makers doing
  exactly this calculation, usually with faster data. When the bot shows
  a big edge, the likeliest explanation is that the model is missing
  something (as happened with the settlement rule above).
- The taker fee peaks at about 1.75% of notional at 50 cents.
- Books are thin at the extremes, so size is often only a handful of shares.
- $68 to $750K is an 11,000x return. The screenshot in the post shows about $3.5K.
- Polymarket blocks trading from a number of countries. Check that it's
  allowed where you live before going further.

## Going live (not implemented)

Real orders would need a Polygon wallet, USDC, Polymarket API credentials and
order signing (Polymarket's `py-clob-client`). That's deliberately left out.
If paper trading shows a consistent, statistically significant profit over a
few thousand trades, that's the point to consider adding it, starting with
tiny stakes.

## Layout

```
polybot/
  markets.py   market discovery, order books, fee formula
  prices.py    Binance public price feed and realised volatility
  model.py     fair-value model for both settlement rules
  strategy.py  value and arbitrage signals
  paper.py     simulated portfolio, persisted to JSON
  engine.py    main loop
  research.py  verify + backtest
  server.py    dashboard server
  static/      dashboard page
tests/         unit tests
```
