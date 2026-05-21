# Adaptive Regime Trader

QQQ trend strategy backtested in Backtrader with walk-forward validation.

## Results

| Metric | Value |
|--------|-------|
| Stock Symbol | QQQ |
| Backtest Period | 2014-01-01 – 2024-12-31 |
| Starting Capital | $100,000 |
| Percentage Return on Capital | 77.06 % |
| Maximum Drawdown | 12.98 % |
| Walk-Forward Analysis Score | 95.10 |
| Robustness Score | 81.33 |


## Approach

I wanted something simple that still respects market regime. QQQ spends long stretches in uptrends, so I only look for entries when price is above the 200-day EMA. On top of that I use RSI for momentum and a short breakout (new high) so I'm not buying every small bounce. Exits are handled with an ATR trailing stop — that kept drawdown reasonable without adding too many rules.

Walk-forward was the harder part. A 6-month test window is too short to warm up a 200 EMA on its own, so I prepend the last ~220 bars from training before each out-of-sample run. Parameters are picked on 2 years of data, but scored on a held-out 30% slice inside that window so I'm not just fitting the full train period.

## Strategy

- **Entry:** close > 200 EMA, RSI(14) > threshold, close at N-day high
- **Exit:** 2× ATR trailing stop
- **Size:** ~95% of cash per trade
- **WFA:** tune RSI threshold and breakout length on each 2Y train block, test next 6 months

## Robustness score

Weighted mix (must exceed 75): WFE 35%, drawdown 20%, OOS consistency 15%, parameter stability 20%, Sharpe 10%. WFE uses annualized in-sample vs out-of-sample returns per window, then `0.6 × median + 0.4 × mean` across windows.

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
