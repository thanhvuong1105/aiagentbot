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

    equity = 10000.0
    position = False
    entry_price = 0.0

    trades = []
    equity_curve = []

    warmup = max(fast_len, slow_len)

    for i in range(len(df)):
        row = df.iloc[i]

        if i < warmup:
            equity_curve.append({"time": str(row["time"]), "equity": equity})
            continue

        prev = df.iloc[i - 1]
        price = row["close"]

        # ===== EXIT =====
        if position:
            if crossed_down(prev["emaFast"], prev["emaSlow"], row["emaFast"], row["emaSlow"]):
                pnl = price - entry_price
                equity += pnl

                trades.append({
                    "side": "long",
                    "entry": entry_price,
                    "exit": price,
                    "pnl": pnl
                })

                position = False

        # ===== ENTRY =====
        if not position:
            if crossed_up(prev["emaFast"], prev["emaSlow"], row["emaFast"], row["emaSlow"]):
                position = True
                entry_price = price

        equity_curve.append({"time": str(row["time"]), "equity": equity})

    return {
        "summary": {
            "netProfit": equity - 10000,
            "totalTrades": len(trades)
        },
        "equityCurve": equity_curve,
        "trades": trades
    }


if __name__ == "__main__":
    raw = sys.stdin.read()
    strategy = json.loads(raw)
    result = run_backtest(strategy)
    print(json.dumps(result))
