# engine/backtest_engine.py

import json
import sys
import pandas as pd
from data_loader import load_csv

def run_backtest(strategy):
    symbol = strategy["meta"]["symbols"][0]
    timeframe = strategy["meta"]["timeframe"]

    df = load_csv(symbol, timeframe)

    equity = 10000
    position = None
    entry_price = 0
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        price = row["close"]

        # ===== ENTRY =====
        if position is None:
            # MOCK condition (sẽ thay bằng eval strategy)
            if i == 1:
                position = "long"
                entry_price = price

        # ===== EXIT =====
        elif position == "long":
            if price >= entry_price * 1.03:
                pnl = price - entry_price
                equity += pnl

                trades.append({
                    "side": "long",
                    "entry": entry_price,
                    "exit": price,
                    "pnl": pnl
                })

                position = None

        equity_curve.append({
            "time": str(row["time"]),
            "equity": equity
        })

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
