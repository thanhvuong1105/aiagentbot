# engine/backtest_engine.py
import json
import sys
import pandas as pd

from data_loader import load_csv, align_htf
from indicators import ema, rsi

def run_backtest(strategy):
    symbol = strategy["meta"]["symbols"][0]
    timeframe = strategy["meta"]["timeframe"]

    df = load_csv(symbol, timeframe)
    df_ltf = load_csv(symbol, "30m")
    df_htf = load_csv(symbol, strategy["htf"]["timeframe"])


    # ===== Indicators =====
    ind = strategy["indicators"]
    df["emaFast"] = ema(df["close"], ind["emaFast"]["length"])
    df["emaSlow"] = ema(df["close"], ind["emaSlow"]["length"])
    df["rsi"] = rsi(df["close"], ind["rsi"]["length"])
    df_htf["emaHTF"] = ema(df_htf["close"], ind["emaHTF"]["length"])
    df_htf_aligned = align_htf(df_ltf, df_htf)



    equity = 10000
    position = None
    entry_price = 0
    sl = tp = None

    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]

        # bỏ bar đầu khi indicator chưa đủ
        if i < 200:
            equity_curve.append({"time": str(row["time"]), "equity": equity})
            continue

        price = row["close"]

        context = {
            "emaFast": row["emaFast"],
            "emaSlow": row["emaSlow"],
            "rsi": row["rsi"],
            "emaHTF": df_htf_aligned.iloc[i]["emaHTF"]
        }

        # ===== EXIT =====
        if position == "long":
            if row["low"] <= sl:
                pnl = sl - entry_price
                equity += pnl
                trades.append({"side": "long", "entry": entry_price, "exit": sl, "pnl": pnl})
                position = None

            elif row["high"] >= tp:
                pnl = tp - entry_price
                equity += pnl
                trades.append({"side": "long", "entry": entry_price, "exit": tp, "pnl": pnl})
                position = None

        elif position == "short":
            if row["high"] >= sl:
                pnl = entry_price - sl
                equity += pnl
                trades.append({"side": "short", "entry": entry_price, "exit": sl, "pnl": pnl})
                position = None

            elif row["low"] <= tp:
                pnl = entry_price - tp
                equity += pnl
                trades.append({"side": "short", "entry": entry_price, "exit": tp, "pnl": pnl})
                position = None

        # ===== ENTRY =====
        htf_ok = eval(strategy["htf"]["filter"], {}, context)

        if position is None and htf_ok:
            if eval(strategy["entry"]["long"], {}, context):
                position = "long"
                entry_price = price
                sl = price * (1 - strategy["exit"]["sl_pct"])
                tp = price + (price - sl) * strategy["exit"]["rr"]

            elif eval(strategy["entry"]["short"], {}, context):
                position = "short"
                entry_price = price
                sl = price * (1 + strategy["exit"]["sl_pct"])
                tp = price - (sl - price) * strategy["exit"]["rr"]

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
