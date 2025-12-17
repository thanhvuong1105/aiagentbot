# engine/data_loader.py
import pandas as pd

def load_csv(symbol: str, timeframe: str):
    filename = f"engine/data/{symbol}_{timeframe}.csv"
    df = pd.read_csv(filename)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def align_htf(df_ltf, df_htf):
    """
    Align HTF to LTF giống TradingView (no repaint)
    """
    df_htf = df_htf.copy()
    df_htf = df_htf.set_index("time")

    htf_aligned = []

    for t in df_ltf["time"]:
        past_htf = df_htf[df_htf.index <= t]
        if len(past_htf) == 0:
            htf_aligned.append(None)
        else:
            htf_aligned.append(past_htf.iloc[-1])

    return pd.DataFrame(htf_aligned)
