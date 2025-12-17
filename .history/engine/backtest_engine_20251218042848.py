# engine/backtest_engine.py

import json

def run_backtest(strategy):
    """
    MOCK backtest engine
    Sau này sẽ thay bằng backtest thật
    """

    result = {
        "summary": {
            "netProfit": 1234,
            "winRate": 0.55,
            "maxDrawdown": -0.12,
            "profitFactor": 1.6,
            "totalTrades": 42
        },
        "equityCurve": [
            {"time": "2023-01-01", "equity": 10000},
            {"time": "2023-02-01", "equity": 10500},
            {"time": "2023-03-01", "equity": 11234}
        ],
        "trades": [
            {
                "side": "long",
                "entryPrice": 20000,
                "exitPrice": 21000,
                "pnl": 1000
            }
        ]
    }

    return result


if __name__ == "__main__":
    # test local
    mock_strategy = {
        "meta": {"name": "test strategy"}
    }

    output = run_backtest(mock_strategy)
    print(json.dumps(output, indent=2))
