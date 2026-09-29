# Results Analysis

Actual output from running `backtester.py` on SPY, 2015/2017/2021/2022.

## Raw Results

| Year | Regime | Strategy Return | Buy & Hold | Max Drawdown | Trades | Final Value |
|------|--------|-----------------|------------|--------------|--------|--------------|
| 2015 | Choppy/sideways | **-5.10%** | +2.31% | -8.07% | 4 | $9,490.38 |
| 2017 | Bull | **+5.87%** | +20.78% | -1.23% | 1 | $10,587.08 |
| 2021 | High-vol bull | **+4.99%** | +30.84% | -4.89% | 1 | $10,498.90 |
| 2022 | Bear | **-1.82%** | -18.65% | -1.82% | 2 | $9,817.73 |

## What Actually Happened

**Bull markets (2017, 2021): the strategy left most of the gains on the table.**
In 2017, buy-and-hold returned +20.78%. The strategy only captured +5.87% — less than a third of it. Same story in 2021 (+30.84% vs +4.99%). The moving average crossover is inherently lagging: by the time the 20-day MA confirms an uptrend, a meaningful chunk of the move has already happened. With only 1 trade executed in each of these years, the strategy essentially caught the tail end of the rally, not the run.

**Bear market (2022): this is where the strategy earned its keep.**
Buy-and-hold lost -18.65%. The strategy lost only -1.82% — a 16.8 percentage point difference. The stop-loss and the crossover sell signal did their job here: getting out of the position early and staying out avoided the bulk of the crash. This is the core value proposition of a trend-following strategy — it's not about beating the market on the way up, it's about not riding it all the way down.

**Choppy market (2015): this is the strategy's weak point.**
Buy-and-hold actually made +2.31% in 2015 (a mild grind upward), but the strategy lost -5.10% with the worst drawdown of any year tested (-8.07%). With 4 trades — the most of any year — this is a textbook whipsaw: the MA crossover kept firing false signals as price oscillated, causing the strategy to buy high and sell low repeatedly. Transaction costs on 4 round-trip-ish trades also ate into returns.

## Honest Conclusion

This strategy is not a return-maximizer — it's a **risk-reducer**. It systematically underperforms buy-and-hold in strong trending bull markets because it enters late and exits early. Its real edge shows up in bear markets, where limiting downside matters more than capturing every point of upside. Its biggest weakness is sideways, choppy markets, where the crossover signal generates noise trades that lose money on both the whipsaws and the transaction costs.

In practice, a strategy like this would need either:
- A trend filter to avoid trading in choppy/low-volatility regimes, or
- A longer-term crossover (e.g., 50/200) to reduce whipsaw frequency, at the cost of even more lag in bull markets
