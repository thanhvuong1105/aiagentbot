# engine/data_loader.py

import pandas as pd

def load_csv(symbol: str, timeframe: str):
    """
    Load OHLC CSV
    File name format: BTCUSDT_30m.csv
    """
    filename = f"engine/data/{symbol}_{timeframe}.csv"
    df = pd.read_csv(filename)

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    return df
