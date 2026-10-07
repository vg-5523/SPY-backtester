# V3 Results Analysis

Results from running `backtester_v3.py` with Yahoo Finance adjusted daily prices through 2026-10-07. Each fixed strategy starts with $10,000 at the beginning of its evaluation window. Historical results can change as the data provider revises data.

## Method

V3 downloads adjusted prices for SPY, QQQ, IWM, TLT, GLD, and SHY, then makes target-weight decisions at each month's final trading date. Signals are delayed before their target weights earn daily returns. A 0.1% fee is charged on the absolute change in portfolio weights. Positions are long-only, fully invested among the selected ETFs, and unleveraged.

The fixed strategies are evaluated from 2005. The walk-forward selector is evaluated from 2008; it selects monthly using only the preceding 756 trading days. Its training score is trailing CAGR minus 0.25 times the absolute trailing maximum drawdown. Before enough history is available, it holds SHY.

## Fixed Strategies, 2005-2026

| Strategy | CAGR | Total Return | Max Drawdown | Final Value |
|---|---:|---:|---:|---:|
| 12-Month Dual Momentum | **11.57%** | **979.50%** | -32.86% | **$107,950.18** |
| 6+12-Month Top 1 | 11.28% | 920.01% | -32.30% | $102,001.35 |
| SPY Buy & Hold | 10.93% | 852.65% | -55.19% | $95,265.08 |
| SPY 50/200 Crossover | 9.37% | 600.50% | -33.72% | $70,049.52 |
| 6+12-Month Top 2 | 9.30% | 590.07% | -29.06% | $69,006.79 |
| SPY 200-Day Trend | 8.90% | 537.49% | -29.59% | $63,748.90 |
| SPY 15% Volatility Target | 8.65% | 506.78% | -23.31% | $60,678.11 |
| SPY Trend Pullback | 5.58% | 225.14% | -7.35% | $32,513.99 |
| SHY Defensive | 1.94% | 51.85% | -5.71% | $15,185.05 |
| SPY 55-Day Breakout | 1.57% | 40.22% | -17.77% | $14,021.96 |

The 12-month dual-momentum rule had the highest fixed-strategy final value over this full period, and lower maximum drawdown than SPY buy-and-hold. This is a historical comparison, not proof that the strategy will continue to outperform.

## Window Checks

| Evaluation Window | Best Fixed Strategy | Strategy CAGR | SPY CAGR | Result |
|---|---|---:|---:|---|
| 2015-2026 | SPY Buy & Hold | 13.83% | 13.83% | SPY led the tested alternatives |
| 2020-2026 | 6+12-Month Top 1 | 17.60% | 15.53% | Momentum selection led SPY |

Different windows produce different winners. In particular, the best full-history rule, 12-month dual momentum, had a 6.94% CAGR from 2015 onward versus 13.83% for SPY.

## Walk-Forward Selector, 2008-2026

| Portfolio | CAGR | Total Return | Max Drawdown | Final Value |
|---|---:|---:|---:|---:|
| V3 Selector | 9.04% | 405.80% | -27.56% | $50,580.47 |
| SPY Buy & Hold | 11.32% | 646.08% | -51.87% | $74,607.65 |

The selector reduced historical drawdown relative to SPY but did not beat it on CAGR or final value. It frequently selected SPY buy-and-hold or 12-month dual momentum, but switching among past winners did not improve the result in this sample.

## Limitations

- The strategy family and scoring rule were designed by inspecting historical results; the reported windows are not a pristine independent holdout.
- The walk-forward process uses past returns for selection, but that does not eliminate overfitting or guarantee future performance.
- A 0.1% turnover fee is modeled. Slippage, taxes, market impact, data delays, and execution failures are not.
- The backtest assumes month-end prices and daily adjusted-close series accurately represent executable prices.
- The asset universe is fixed to ETFs with available history; these results do not establish performance on other assets or future market regimes.

## Conclusion

V3 is the most complete research tool in this project, but it does not establish a reliable buy-and-hold beater. The full-period leader changes across windows, and the walk-forward selector underperformed SPY from 2008. The defensible takeaway is that some rules reduced drawdown in this sample; none can be assumed to make more money in the future.
