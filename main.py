import backtrader as bt

from analysis.robustness import compute_robustness
from config import COMMISSION, EMA_PERIOD, END_DATE, INITIAL_CASH, START_DATE, SYMBOL
from data.fetch_data import fetch_data
from strategies.regime_strategy import RegimeStrategy
from walk_forward.walk_forward import run_backtest, walk_forward_analysis


def run_full_backtest(data, cash=INITIAL_CASH):
    cerebro = bt.Cerebro()
    cerebro.adddata(bt.feeds.PandasData(dataname=data))
    cerebro.addstrategy(RegimeStrategy)
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=COMMISSION)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")

    results = cerebro.run()
    strat = results[0]
    final_value = cerebro.broker.getvalue()
    dd = strat.analyzers.drawdown.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")

    return {
        "final_value": final_value,
        "total_return": ((final_value - cash) / cash) * 100,
        "max_drawdown": dd.max.drawdown or 0.0,
        "sharpe": float(sharpe) if sharpe is not None else None,
    }


def parameter_sensitivity(data, cash=INITIAL_CASH):
    base = run_full_backtest(data, cash)["total_return"]

    def variant(**params):
        res = run_backtest(data, cash, strategy_params=params)
        return ((res["final_value"] - cash) / cash) * 100

    variants = [
        variant(rsi_threshold=50),
        variant(rsi_threshold=60),
        variant(breakout_period=15),
        variant(breakout_period=25),
        variant(ema_period=max(50, EMA_PERIOD - 25)),
    ]
    return base, variants


def main():
    data = fetch_data(SYMBOL, START_DATE, END_DATE)
    backtest = run_full_backtest(data)
    wfa = walk_forward_analysis(data)
    wfa_score = wfa.attrs.get("wfa_score", 0.0) if not wfa.empty else 0.0

    base_return, variant_returns = parameter_sensitivity(data)
    robustness, _ = compute_robustness(
        avg_wfe=wfa_score,
        max_drawdown_pct=backtest["max_drawdown"],
        wfa_df=wfa,
        base_return_pct=base_return,
        variant_returns_pct=variant_returns,
        sharpe_ratio=backtest["sharpe"],
    )

    print(f"Symbol: {SYMBOL} | Period: {START_DATE} to {END_DATE} | Capital: ${INITIAL_CASH:,.0f}")
    print(f"Percentage Return on Capital: {backtest['total_return']:.2f} %")
    print(f"Maximum Drawdown: {backtest['max_drawdown']:.2f} %")
    print(f"Walk-Forward Analysis Score: {wfa_score:.2f}")
    print(f"Robustness Score: {robustness:.2f}")
    print("Repo: https://github.com/Debashis7307/adaptive-regime-trader")


if __name__ == "__main__":
    main()
