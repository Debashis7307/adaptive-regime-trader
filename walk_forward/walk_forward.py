import backtrader as bt
import pandas as pd

from config import (
    ATR_PERIOD,
    BREAKOUT_PERIOD,
    COMMISSION,
    EMA_PERIOD,
    RSI_PERIOD,
    TEST_MONTHS,
    TRAIN_YEARS,
)
from strategies.regime_strategy import RegimeStrategy
from utils.metrics import calculate_return, summarize_wfa_efficiency, walk_forward_efficiency

TRAIN_SIZE = TRAIN_YEARS * 252
TEST_SIZE = TEST_MONTHS * 21
WARMUP_BARS = max(EMA_PERIOD, RSI_PERIOD, ATR_PERIOD, BREAKOUT_PERIOD, 30) + 10

RSI_GRID = (45, 50, 55)
BREAKOUT_GRID = (15, 20, 25)


def run_backtest(data, cash, strategy_params=None, trade_start=None):
    cerebro = bt.Cerebro()
    cerebro.adddata(bt.feeds.PandasData(dataname=data))

    params = dict(strategy_params or {})
    if trade_start is not None:
        params["trade_start"] = trade_start

    cerebro.addstrategy(RegimeStrategy, **params)
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=COMMISSION)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")

    results = cerebro.run()
    strat = results[0]
    dd = strat.analyzers.drawdown.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")

    return {
        "final_value": cerebro.broker.getvalue(),
        "max_drawdown": dd.max.drawdown or 0.0,
        "sharpe": float(sharpe) if sharpe is not None else 0.0,
    }


def _score(cash, result):
    ret = calculate_return(cash, result["final_value"])
    return ret + result["sharpe"] * 12 - result["max_drawdown"] * 0.25


def optimize_on_train(train, cash):
    best_params = {"rsi_threshold": 50, "breakout_period": BREAKOUT_PERIOD}
    best_score = float("-inf")

    split = int(len(train) * 0.7)
    opt_train = train.iloc[:split]
    val_warmup = train.iloc[max(0, split - WARMUP_BARS) : split]
    val_hold = train.iloc[split:]
    val_data = pd.concat([val_warmup, val_hold])
    val_start = val_hold.index[0].date()

    for rsi_th in RSI_GRID:
        for breakout in BREAKOUT_GRID:
            params = {"rsi_threshold": rsi_th, "breakout_period": breakout}
            opt_res = run_backtest(opt_train, cash, strategy_params=params)
            val_res = run_backtest(val_data, cash, strategy_params=params, trade_start=val_start)
            score = 0.35 * _score(cash, opt_res) + 0.65 * _score(cash, val_res)
            if score > best_score:
                best_score = score
                best_params = params

    is_res = run_backtest(train, cash, strategy_params=best_params)
    return best_params, calculate_return(cash, is_res["final_value"])


def walk_forward_analysis(data, train_size=TRAIN_SIZE, test_size=TEST_SIZE, cash=100000):
    results = []
    start = 0

    while start + train_size + test_size <= len(data):
        train = data.iloc[start : start + train_size]
        test = data.iloc[start + train_size : start + train_size + test_size]

        best_params, in_return = optimize_on_train(train, cash)
        combined = pd.concat([train.iloc[-WARMUP_BARS:], test])

        oos = run_backtest(
            combined,
            cash,
            strategy_params=best_params,
            trade_start=test.index[0].date(),
        )
        out_return = calculate_return(cash, oos["final_value"])

        results.append({
            "in_sample_return": in_return,
            "out_sample_return": out_return,
            "efficiency": walk_forward_efficiency(out_return, in_return),
        })

        start += test_size

    df = pd.DataFrame(results)
    if not df.empty:
        df.attrs["wfa_score"] = summarize_wfa_efficiency(df["efficiency"])
    return df
