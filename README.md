# Stock Backtester Research

A Python project for comparing rule-based ETF strategies with historical data. V1 preserves the original SPY backtest, V2 compares trend and momentum variants, and V3 evaluates a broader strategy family with walk-forward selection.

## Versions

### V1: Original (`backtester.py`)

- Tests SPY using 20-, 50-, and 200-day moving averages, volatility-based sizing, a 5% stop-loss, and a 0.1% transaction fee.
- Uses same-close signals and fills, which can overstate realistic performance because the close is not known until that close has occurred.
- Runs the selected years 2015, 2017, 2021, and 2022.

### V2: Strategy comparison (`backtester_v2.py`)

- Compares a 20/50/200-day baseline with a trend-and-126-day-momentum strategy on SPY.
- Tests 12% and 20% annualized volatility targets, capped at 100% invested.
- Signals use the previous close; orders are modeled at the next session's close. A prior-year data warmup is used for indicators.
- Also tests diversified and concentrated monthly ETF rotations across SPY, QQQ, IWM, TLT, and GLD, with SHY as the defensive holding.

### V3: Strategy research (`backtester_v3.py`)

V3 compares ten monthly strategies across SPY, QQQ, IWM, TLT, GLD, and SHY:

- SPY buy-and-hold and SHY defensive
- SPY 200-day trend, 50/200-day crossover, and 15% volatility target
- 12-month dual momentum and blended 6-/12-month momentum selecting one or two ETFs
- SPY 55-day breakout and RSI-based trend pullback

The walk-forward selector chooses a candidate monthly using only its prior 756 trading days. Its score is trailing annualized growth minus 0.25 times the absolute trailing maximum drawdown. It trades the selected candidate with delayed weights rather than same-close fills.

## V3 Assumptions And Metrics

- Yahoo Finance adjusted daily close data, with `auto_adjust=True`.
- Initial portfolio value: $10,000.
- Monthly target weights; no leverage and no short positions.
- Transaction fee: 0.1% multiplied by the sum of absolute portfolio-weight changes at rebalance.
- Reports CAGR, total return, maximum drawdown, final value, and comparisons to dividend-adjusted SPY.
- Evaluates fixed strategies from 2005, window checks from 2015 and 2020, and the selector from 2008.

Transaction fees are modeled, but slippage, taxes, market impact, and execution failures are not. Historical results are not a guarantee of future performance.

## Setup

```bash
pip install yfinance pandas numpy matplotlib
python backtester.py
python backtester_v2.py
python backtester_v3.py
```

Run the script for the version you want. V1 and V2 save their own comparison charts. V3 saves `backtester_v3_results.png`.

## Latest V3 Result

Yahoo Finance data downloaded through 2026-10-07 showed 12-month dual momentum leading the fixed strategies from 2005, with an 11.57% CAGR versus 10.93% for SPY. SPY buy-and-hold led from 2015 onward, and the walk-forward selector trailed SPY from 2008 onward. The detailed results and caveats are in [ANALYSIS.md](ANALYSIS.md).

## Author

Vrishin Gera — [GitHub](https://github.com/vg-5523)
