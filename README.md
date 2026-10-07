# Stock Backtester — Quantitative Trading Strategy

A Python backtesting project with three versions. V1 preserves the original implementation, V2 compares trend-and-momentum variants, and V3 tests a strategy family with walk-forward selection.

## Overview

This project tests whether a simple, rule-based trading strategy would have been profitable across different market conditions — bull markets, bear markets, choppy/sideways markets, and high-volatility periods. It goes beyond a naive backtest by incorporating realistic trading frictions: transaction costs, risk management, and volatility-aware position sizing.

## Strategy Versions

### V1: Original (`backtester.py`)

- Buys when the 20-day moving average is above the 50-day moving average and price is above the 200-day moving average.
- Sells when those trend conditions weaken or the 5% stop-loss is reached.
- Preserves the original same-close execution behavior.

### V2: Advanced comparison (`backtester_v2.py`)

- Compares a baseline version of the V1 rules with the advanced strategy on the same yearly SPY data.
- **Entry:** price above the 200-day average, 50-day average above the 200-day average, and positive 126-day momentum.
- **Exit:** price falls below the 200-day average or 126-day momentum turns negative.
- **Position sizing:** compares 12% and 20% annualized volatility targets, each capped at 100% invested.
- Signals use the prior close and trades execute at the next session's close; the indicator warmup uses the preceding year's data.
- Both compared strategies include a 0.1% transaction fee. This execution model is more conservative than V1's same-close fills.
- Also tests an unleveraged monthly rotation across SPY, QQQ, IWM, TLT, and GLD, using SHY defensively. It ranks positive 6- and 12-month momentum, applies a 200-day trend filter, and reports both diversified and concentrated allocations.
- The long-history benchmark uses dividend-adjusted SPY prices. The recent-period check is diagnostic, not a guarantee of future performance.

### V3: Strategy research (`backtester_v3.py`)

- Compares ten fixed rules across SPY, QQQ, IWM, TLT, GLD, and SHY, including trend, momentum, breakout, pullback, and volatility-target strategies.
- Runs a monthly selector using only the prior 756 trading days; all positions are unleveraged and include a 0.1% turnover fee.
- Reports full-history results, 2015 and 2020 window checks, and walk-forward results against dividend-adjusted SPY.
- Historical results do not establish future outperformance. The selector and candidate rules can underperform buy-and-hold.

## Features

- **Volatility-based position sizing** in the V1 and V2 backtests
- **Risk management** — V1 has a 5% stop-loss; V2 scales exposure to a volatility target
- **Transaction costs** — V2 applies a 0.1% fee to each trade
- **Multi-year stress testing** — strategy is run across four market regimes:
  - **2017** — Bull market (strong uptrend)
  - **2022** — Bear market (major decline)
  - **2015** — Choppy/sideways market
  - **2021** — High-volatility bull market

## Metrics Reported

For each year tested:
- Total strategy return (%)
- Buy-and-hold benchmark return (%)
- Maximum drawdown (%)
- Number of trades executed
- Win rate (%)
- Final portfolio value

## Tech Stack

- **Python 3**
- `yfinance` — historical price data
- `pandas` / `numpy` — data processing and calculations
- `matplotlib` — visualization

## Setup

```bash
pip install yfinance pandas numpy matplotlib
python backtester.py
python backtester_v2.py
python backtester_v3.py
```

Run `backtester.py` for V1, `backtester_v2.py` for V2, or `backtester_v3.py` for the strategy-family and walk-forward comparison. V3 saves `backtester_v3_results.png`.

## Sample Output

```
BACKTESTER V2: SPY | 0.1% Fee | Next-session close execution
================================================================

YEAR 2017:
  Baseline  Return   X.XX% | Drawdown   X.XX% | Trades   X | Final $XX,XXX.XX
  Advanced  Return   X.XX% | Drawdown   X.XX% | Trades   X | Final $XX,XXX.XX
  Buy & Hold Return:   X.XX%
```

## Key Takeaways

Backtesting cannot guarantee that a strategy will beat buy-and-hold. V3's 12-month momentum rule beat SPY over 2005-2026, but buy-and-hold led the tested strategies from 2015; the walk-forward selector also trailed SPY. Fees are modeled, but slippage, taxes, and market impact are not.

## Future Improvements

- Add additional signals (RSI, Bollinger Bands) for comparison
- Test across multiple tickers, not just SPY
- Incorporate slippage modeling
- Parameter optimization (grid search over MA windows)

## Author

Vrishin Gera — [GitHub](https://github.com/vg-5523)
