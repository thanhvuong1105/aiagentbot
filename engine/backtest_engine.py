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


# ===== METRICS =====
def calc_winrate(trades):
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return round(wins / len(trades) * 100, 2)


def calc_profit_factor(trades):
    gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    if gross_loss == 0:
        return round(float("inf"), 2)
    return round(gross_profit / gross_loss, 2)


def calc_max_drawdown(equity_curve):
    peak = -1e18
    max_dd = 0.0
    for p in equity_curve:
        equity = p["equity"]
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd * 100, 2)


def run_backtest(strategy):
    symbol = strategy["meta"]["symbols"][0]
    timeframe = strategy["meta"]["timeframe"]

    fast_len = strategy["indicators"]["emaFast"]["length"]
    slow_len = strategy["indicators"]["emaSlow"]["length"]

    # ===== COST CONFIG (2B) =====
    fee_rate = strategy.get("costs", {}).get("fee", 0.0004)
    slippage = strategy.get("costs", {}).get("slippage", 0.0001)

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
        price = float(row["close"])

        if i < warmup:
            equity_curve.append({"time": time, "equity": round(equity, 6)})
            continue

        prev = df.iloc[i - 1]

        # ===== EXIT (LONG) =====
        if in_position:
            if crossed_down(prev["emaFast"], prev["emaSlow"], row["emaFast"], row["emaSlow"]):
                exit_price = price * (1 - slippage)
                gross_pnl = exit_price - current_trade["entry_price"]
                exit_fee = exit_price * fee_rate
                pnl = gross_pnl - exit_fee

                equity += pnl

                current_trade["exit_time"] = time
                current_trade["exit_price"] = round(exit_price, 6)
                current_trade["exit_fee"] = round(exit_fee, 6)
                current_trade["pnl"] = round(pnl, 6)

                trades.append(current_trade)
                current_trade = None
                in_position = False

        # ===== ENTRY (LONG) =====
        if not in_position:
            if crossed_up(prev["emaFast"], prev["emaSlow"], row["emaFast"], row["emaSlow"]):
                entry_price = price * (1 + slippage)
                entry_fee = entry_price * fee_rate
                equity -= entry_fee

                current_trade = {
                    "side": "Long",
                    "entry_time": time,
                    "entry_price": round(entry_price, 6),
                    "entry_fee": round(entry_fee, 6)
                }
                in_position = True

        equity_curve.append({"time": time, "equity": round(equity, 6)})

    # ===== METRICS (2C) =====
    winrate = calc_winrate(trades)
    profit_factor = calc_profit_factor(trades)
    max_dd = calc_max_drawdown(equity_curve)

    result = {
        "summary": {
            "initialEquity": initial_equity,
            "finalEquity": round(equity, 6),
            "netProfit": round(equity - initial_equity, 6),
            "totalTrades": len(trades),
            "winrate": winrate,
            "profitFactor": profit_factor,
            "maxDrawdownPct": max_dd
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
# LEVEL_2C_CONFIRMED
