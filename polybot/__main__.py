"""Command line entry point: python -m polybot <command>."""

import argparse
import json
import logging
import threading
import time

from .markets import ASSETS, TIMEFRAMES
from .strategy import Config


def _csv(value, allowed):
    items = [v.strip().lower() for v in value.split(",") if v.strip()]
    bad = [v for v in items if v not in allowed]
    if bad:
        raise argparse.ArgumentTypeError(f"unknown {bad}; choose from {sorted(allowed)}")
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(prog="polybot", description="Paper-trade Polymarket crypto Up/Down markets.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def market_args(p, default_tf="5m,15m,1h,4h"):
        p.add_argument("--assets", default="btc,eth,sol,xrp", type=lambda v: _csv(v, ASSETS))
        p.add_argument("--timeframes", default=default_tf, type=lambda v: _csv(v, TIMEFRAMES))

    run = sub.add_parser("run", help="run the paper-trading loop with a web dashboard")
    market_args(run)
    run.add_argument("--interval", type=float, default=5.0, help="seconds between cycles")
    run.add_argument("--port", type=int, default=8765, help="dashboard port (0 disables)")
    run.add_argument("--host", default="0.0.0.0")
    run.add_argument("--state", default="state/paper.json", help="paper portfolio file")
    run.add_argument("--cash", type=float, default=100.0, help="starting paper cash")
    run.add_argument("--min-edge", type=float, default=Config.min_edge)
    run.add_argument("--stake", type=float, default=Config.stake_usd)
    run.add_argument("--max-position", type=float, default=Config.max_position_usd)
    run.add_argument("--vol-mult", type=float, default=1.0, help="scale realised vol (calibrate with backtest --sweep)")
    run.add_argument("--cycles", type=int, default=0, help="stop after N cycles (0 = forever)")

    scan = sub.add_parser("scan", help="print one snapshot of live markets and fair values")
    market_args(scan)

    ver = sub.add_parser("verify", help="check the settlement rule against resolved markets")
    ver.add_argument("--asset", default="btc", choices=sorted(ASSETS))
    ver.add_argument("--timeframe", default="5m", choices=["5m", "15m"])
    ver.add_argument("--count", type=int, default=30)

    bt = sub.add_parser("backtest", help="replay resolved markets against historical prices")
    bt.add_argument("--asset", default="btc", choices=sorted(ASSETS))
    bt.add_argument("--timeframe", default="15m", choices=["5m", "15m"])
    bt.add_argument("--count", type=int, default=40)
    bt.add_argument("--min-edge", type=float, default=Config.min_edge)
    bt.add_argument("--half-spread", type=float, default=0.01)
    bt.add_argument("--vol-mult", type=float, default=1.0)
    bt.add_argument("--json", action="store_true", help="print every simulated trade")
    bt.add_argument("--sweep", action="store_true", help="also sweep --vol-mult to calibrate it")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    if args.cmd in ("run", "scan"):
        from .engine import Engine
        if args.cmd == "scan":
            eng = Engine(args.assets, args.timeframes, book_path=None, cfg=Config(min_edge=99))
            eng.step()
            _print_rows(eng.rows)
            return
        cfg = Config(min_edge=args.min_edge, stake_usd=args.stake, max_position_usd=args.max_position)
        eng = Engine(args.assets, args.timeframes, cfg=cfg, book_path=args.state, starting_cash=args.cash,
                     vol_mult=args.vol_mult)
        if args.port:
            from .server import serve
            serve(eng, args.host, args.port)
            logging.info("dashboard on http://%s:%d", "localhost" if args.host == "0.0.0.0" else args.host, args.port)
        logging.info("PAPER TRADING ONLY. No real orders are sent.")
        stop = threading.Event()
        if args.cycles:
            done = [0]
            orig = eng.step

            def counted(now=None):
                orig(now)
                done[0] += 1
                if done[0] >= args.cycles:
                    stop.set()
            eng.step = counted
        try:
            eng.run(args.interval, stop)
        except KeyboardInterrupt:
            pass
        print(json.dumps(eng.book.summary(), indent=1))

    elif args.cmd == "verify":
        from .research import verify
        n, tally = verify(args.asset, args.timeframe, args.count)
        print(f"{n} resolved {args.asset} {args.timeframe} markets")
        for rule, hits in tally.items():
            print(f"  {rule:32s} {hits}/{n}")

    elif args.cmd == "backtest":
        from .research import load_windows, replay
        windows = load_windows(args.asset, args.timeframe, args.count,
                               progress=lambda s: print("  loaded", s, flush=True))
        res = replay(windows, args.min_edge, args.half_spread, args.vol_mult)
        detail = res.pop("detail")
        print(json.dumps(res, indent=1))
        if args.json:
            print(json.dumps(detail, indent=1))
        if args.sweep:
            print(f"\n{'vol_mult':>8s} {'brier':>7s} {'market':>7s} {'trades':>6s} {'pnl':>8s} {'+/-1se':>7s}")
            for vm in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4):
                r = replay(windows, args.min_edge, args.half_spread, vm)
                print(f"{vm:8.1f} {r['brier_model']:7.4f} {r['brier_market']:7.4f} {r['trades']:6d} "
                      f"{r['pnl_per_share_total']:8.2f} {r['pnl_std_error']:7.2f}")


def _print_rows(rows):
    head = f"{'market':10s} {'res':5s} {'ends':>6s} {'spot':>11s} {'strike':>11s} {'fair':>6s} {'up ask':>7s} {'dn ask':>7s} {'edge up':>8s} {'edge dn':>8s}"
    print(head)
    print("-" * len(head))
    f = lambda v, d=3: "-" if v is None else f"{v:.{d}f}"
    for r in rows:
        d = 4 if (r.get("spot") or 0) < 10 else 2
        print(f"{r['asset'] + ' ' + r['timeframe']:10s} {r['resolution']:5s} {r['ends_in']:6.0f} "
              f"{f(r.get('spot'), d):>11s} {f(r.get('strike'), d):>11s} {f(r.get('fair_up')):>6s} "
              f"{f(r.get('up_ask'), 2):>7s} {f(r.get('down_ask'), 2):>7s} {f(r.get('edge_up')):>8s} {f(r.get('edge_down')):>8s}"
              + (f"  ERROR {r['error']}" if r.get("error") else ""))


if __name__ == "__main__":
    main()
