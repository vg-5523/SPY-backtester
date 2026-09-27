# Stock Backtester — Quantitative Trading Strategy

A Python backtesting framework that simulates a moving average crossover trading strategy on historical S&P 500 (SPY) data, stress-tested across four distinct market regimes.

## Overview

This project tests whether a simple, rule-based trading strategy would have been profitable across different market conditions — bull markets, bear markets, choppy/sideways markets, and high-volatility periods. It goes beyond a naive backtest by incorporating realistic trading frictions: transaction costs, risk management, and volatility-aware position sizing.

## Strategy

**20/50 Moving Average Crossover**
- **Buy signal:** 20-day moving average crosses above the 50-day moving average
- **Sell signal:** 20-day moving average crosses below the 50-day moving average

## Features

- **Volatility-based position sizing** — position size scales inversely with recent volatility (smaller bets in turbulent markets, larger bets in calm ones)
- **Risk management** — automatic 5% stop-loss on every open position
- **Transaction costs** — 0.1% fee applied to every trade, to reflect realistic execution costs
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
```

Running the script fetches historical data, runs the backtest across all four test years, prints a results summary, and saves a chart (`backtester_results.png`) comparing portfolio performance across market conditions.

## Sample Output

```
BACKTESTER: SPY | MA 20/50 Crossover | 0.1% Fee | 5% Stop Loss
================================================================

YEAR 2017:
  Strategy Return:      X.XX%
  Buy & Hold Return:    X.XX%
  Max Drawdown:         X.XX%
  Total Trades:         X
  Final Value:          $X,XXX.XX
```

## Key Takeaways

Backtesting a strategy on a single favorable year can be misleading. Testing the same strategy across bull, bear, choppy, and volatile years reveals how sensitive it is to market regime — and whether real-world frictions like transaction costs and stop-losses meaningfully change the outcome.

## Future Improvements

- Add additional signals (RSI, Bollinger Bands) for comparison
- Test across multiple tickers, not just SPY
- Incorporate slippage modeling
- Parameter optimization (grid search over MA windows)

## Author

Vrishin Gera — [GitHub](https://github.com/vg-5523)
