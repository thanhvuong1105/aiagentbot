# engine/backtest_engine.py
import json
import sys
import pandas as pd

from data_loader import load_csv
from indicators import ema


def crossed_up(prev_fast, prev_slow, fast, slow):
    return prev_fast <= prev_slow and fast > slow


def crossed_down(prev_fast, prev_slow, fast, slow):
    return prev_fast >= prev_slow and fast < slow


def run_backtest(strategy):
    symbol = strategy["meta"]["symbols"][0]
    timeframe = strategy["meta"]["timeframe"]

    fast_len = strategy["indicators"]["emaFast"]["length"]
    slow_len = strategy["indicators"]["emaSlow"]["length"]

    df = load_csv(symbol, timeframe)

    df["emaFast"] = ema(df["close"], fast_len)
    df["emaSlow"] = ema(df["close"], slow_len)

    # ===== ACCOUNT =====
    initial_equity = 10000.0
    equity = initial_equity

    # ===== STATE =====
    in_position = False
    current_trade = None

    trades = []
    equity_curve = []

    warmup = max(fast_len, slow_len)

    for i in range(len(df)):
        row = df.iloc[i]
        time = str(row["time"])
        price = row["close"]

        # ===== WARMUP =====
        if i < warmup:
            equity_curve.append({
                "time": time,
                "equity": equity
            })
            continue

        prev = df.iloc[i - 1]

        # ===== EXIT (LONG) =====
        if in_position:
            if crossed_down(
                prev["emaFast"], prev["emaSlow"],
                row["emaFast"], row["emaSlow"]
            ):
                exit_price = price
                pnl = exit_price - current_trade["entry_price"]

                equity += pnl

                current_trade["exit_time"] = time
                current_trade["exit_price"] = exit_price
                current_trade["pnl"] = pnl

                trades.append(current_trade)

                current_trade = None
                in_position = False

        # ===== ENTRY (LONG) =====
        if not in_position:
            if crossed_up(
                prev["emaFast"], prev["emaSlow"],
                row["emaFast"], row["emaSlow"]
            ):
                current_trade = {
                    "side": "Long",
                    "entry_time": time,
                    "entry_price": price
                }
                in_position = True

        # ===== EQUITY CURVE =====
        equity_curve.append({
            "time": time,
            "equity": equity
        })

    # ===== SUMMARY (TẠM THỜI) =====
    result = {
        "summary": {
            "initialEquity": initial_equity,
            "finalEquity": equity,
            "netProfit": equity - initial_equity,
            "totalTrades": len(trades)
        },
        "equityCurve": equity_curve,
        "trades": trades
    }

    return result


if __name__ == "__main__":
    raw = sys.stdin.read()
    strategy = json.loads(raw)
    result = run_backtest(strategy)
    print(json.dumps(result))
