import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ASSET_TICKERS = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SHY']
RISK_TICKERS = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD']
TRANSACTION_FEE = 0.001
TEST_START_YEAR = 2005
SELECTOR_START_YEAR = 2008
TRAINING_DAYS = 756
DRAWDOWN_PENALTY = 0.25


def download_adjusted_prices():
    data = yf.download(
        ASSET_TICKERS,
        start='2004-01-01',
        auto_adjust=True,
        progress=False,
        group_by='ticker',
    )
    if data is None or data.empty:
        raise ValueError('No adjusted ETF prices were downloaded.')

    close_prices = {}
    for ticker in ASSET_TICKERS:
        if (ticker, 'Close') in data.columns:
            close_column = (ticker, 'Close')
        elif ('Close', ticker) in data.columns:
            close_column = ('Close', ticker)
        else:
            raise ValueError(f'No adjusted Close column found for {ticker}.')
        close_series = data[close_column]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]
        close_prices[ticker] = pd.to_numeric(close_series, errors='coerce')

    return pd.DataFrame(close_prices).sort_index().ffill().dropna(subset=['SPY'])


def build_candidate_signals(prices):
    strategy_names = [
        'SPY Buy & Hold',
        'SHY Defensive',
        'SPY 200-Day Trend',
        'SPY 50/200 Crossover',
        'SPY 15% Volatility Target',
        '12-Month Dual Momentum',
        '6+12-Month Top 1',
        '6+12-Month Top 2',
        'SPY 55-Day Breakout',
        'SPY Trend Pullback',
    ]
    signals = {
        name: pd.DataFrame(np.nan, index=prices.index, columns=ASSET_TICKERS)
        for name in strategy_names
    }

    sma20 = prices['SPY'].rolling(20).mean()
    sma50 = prices.rolling(50).mean()
    sma200 = prices.rolling(200).mean()
    momentum_6m = prices.pct_change(126)
    momentum_12m = prices.pct_change(252)
    momentum_score = (momentum_6m + momentum_12m) / 2
    spy_annual_volatility = prices['SPY'].pct_change().rolling(20).std() * np.sqrt(252)
    prior_55_day_high = prices['SPY'].rolling(55).max().shift(1)

    daily_change = prices['SPY'].diff()
    average_gain = daily_change.clip(lower=0).rolling(14).mean()
    average_loss = -daily_change.clip(upper=0).rolling(14).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))

    decisions = prices.groupby(prices.index.to_period('M')).tail(1).index
    pullback_active = False

    for date in decisions:
        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        weights['SPY'] = 1.0
        signals['SPY Buy & Hold'].loc[date] = weights

        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        weights['SHY'] = 1.0
        signals['SHY Defensive'].loc[date] = weights

        spy_price = prices.at[date, 'SPY']
        spy_sma200 = sma200.at[date, 'SPY']
        spy_sma50 = sma50.at[date, 'SPY']
        spy_trend = pd.notna(spy_sma200) and spy_price > spy_sma200

        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        weights['SPY' if spy_trend else 'SHY'] = 1.0
        signals['SPY 200-Day Trend'].loc[date] = weights

        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        golden_cross = pd.notna(spy_sma50) and pd.notna(spy_sma200) and spy_sma50 > spy_sma200
        weights['SPY' if golden_cross else 'SHY'] = 1.0
        signals['SPY 50/200 Crossover'].loc[date] = weights

        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        annual_volatility = spy_annual_volatility.at[date]
        if spy_trend and pd.notna(annual_volatility) and annual_volatility > 0:
            spy_weight = min(1.0, 0.15 / annual_volatility)
            weights['SPY'] = spy_weight
            weights['SHY'] = 1.0 - spy_weight
        else:
            weights['SHY'] = 1.0
        signals['SPY 15% Volatility Target'].loc[date] = weights

        eligible = [
            ticker for ticker in RISK_TICKERS
            if pd.notna(sma200.at[date, ticker])
            and prices.at[date, ticker] > sma200.at[date, ticker]
            and pd.notna(momentum_6m.at[date, ticker])
            and pd.notna(momentum_12m.at[date, ticker])
            and momentum_6m.at[date, ticker] > 0
            and momentum_12m.at[date, ticker] > 0
        ]

        ranked_12m = momentum_12m.loc[date, eligible].dropna().nlargest(1)
        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        if ranked_12m.empty:
            weights['SHY'] = 1.0
        else:
            weights[ranked_12m.index[0]] = 1.0
        signals['12-Month Dual Momentum'].loc[date] = weights

        ranked_blended = momentum_score.loc[date, eligible].dropna().nlargest(2)
        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        if ranked_blended.empty:
            weights['SHY'] = 1.0
        else:
            for ticker in ranked_blended.index:
                weights[ticker] = 1.0 / len(ranked_blended)
        signals['6+12-Month Top 2'].loc[date] = weights

        ranked_blended = momentum_score.loc[date, eligible].dropna().nlargest(1)
        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        if ranked_blended.empty:
            weights['SHY'] = 1.0
        else:
            weights[ranked_blended.index[0]] = 1.0
        signals['6+12-Month Top 1'].loc[date] = weights

        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        breakout = pd.notna(prior_55_day_high.at[date]) and spy_price > prior_55_day_high.at[date]
        weights['SPY' if spy_trend and breakout else 'SHY'] = 1.0
        signals['SPY 55-Day Breakout'].loc[date] = weights

        current_rsi = rsi.at[date]
        if pd.notna(current_rsi):
            if not spy_trend or current_rsi >= 70:
                pullback_active = False
            elif current_rsi <= 35:
                pullback_active = True
        weights = {ticker: 0.0 for ticker in ASSET_TICKERS}
        weights['SPY' if pullback_active else 'SHY'] = 1.0
        signals['SPY Trend Pullback'].loc[date] = weights

    return signals


def simulate_returns(prices, monthly_signals):
    filled_signals = monthly_signals.ffill().fillna(0.0)
    execution_weights = filled_signals.shift(1).fillna(0.0)
    holding_weights = execution_weights.shift(1).fillna(0.0)
    asset_returns = prices.pct_change().fillna(0.0)
    turnover = execution_weights.diff().abs().sum(axis=1).fillna(0.0)
    return (holding_weights * asset_returns).sum(axis=1) - turnover * TRANSACTION_FEE


def calculate_metrics(daily_returns, start_year):
    test_returns = daily_returns.loc[daily_returns.index.year >= start_year]
    if test_returns.empty:
        raise ValueError(f'No returns are available from {start_year} onward.')

    equity = 10000.0 * (1 + test_returns).cumprod()
    years = len(test_returns) / 252
    final_value = float(equity.iloc[-1])
    cagr = ((final_value / 10000.0) ** (1 / years) - 1) * 100
    total_return = (final_value / 10000.0 - 1) * 100
    max_drawdown = ((equity / equity.cummax()) - 1).min() * 100
    return {
        'total_return': float(total_return),
        'cagr': float(cagr),
        'max_drawdown': float(max_drawdown),
        'final_value': final_value,
        'equity': equity,
    }


def walk_forward_selector(prices, signals, candidate_returns):
    selector_signals = pd.DataFrame(np.nan, index=prices.index, columns=ASSET_TICKERS)
    month_ends = prices.groupby(prices.index.to_period('M')).tail(1).index
    selected_strategies = {}
    candidate_names = list(signals)

    for date in month_ends:
        history_end = prices.index.get_loc(date)
        history_start = history_end - TRAINING_DAYS + 1
        if date.year < SELECTOR_START_YEAR or history_start < 0:
            selected_name = 'SHY Defensive'
        else:
            training_returns = candidate_returns.iloc[history_start:history_end + 1]
            scores = {}
            for name in candidate_names:
                series = training_returns[name]
                training_equity = (1 + series).cumprod()
                training_cagr = training_equity.iloc[-1] ** (252 / len(series)) - 1
                training_drawdown = ((training_equity / training_equity.cummax()) - 1).min()
                scores[name] = training_cagr - DRAWDOWN_PENALTY * abs(training_drawdown)
            selected_name = max(scores, key=scores.get)

        selector_signals.loc[date] = signals[selected_name].loc[date].fillna(0.0)
        if date.year >= SELECTOR_START_YEAR:
            selected_strategies[date] = selected_name

    selector_returns = simulate_returns(prices, selector_signals)
    selection_counts = pd.Series(selected_strategies).value_counts()
    return selector_returns, selection_counts


def main():
    prices = download_adjusted_prices()
    signals = build_candidate_signals(prices)
    candidate_returns = pd.DataFrame({
        name: simulate_returns(prices, monthly_signals)
        for name, monthly_signals in signals.items()
    })
    benchmark_metrics = calculate_metrics(candidate_returns['SPY Buy & Hold'], TEST_START_YEAR)

    print(f"V3 STRATEGY RESEARCH | {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"Assets: {', '.join(ASSET_TICKERS)} | Monthly decisions | {TRANSACTION_FEE:.1%} turnover fee | No leverage")
    print("Fixed strategy results from 2005:")
    print("Strategy                         CAGR    Total Return    Max DD        Final       vs SPY")

    fixed_metrics = {}
    for name in candidate_returns.columns:
        metrics = calculate_metrics(candidate_returns[name], TEST_START_YEAR)
        fixed_metrics[name] = metrics
        beats_spy = metrics['final_value'] > benchmark_metrics['final_value']
        print(
            f"{name:<31} {metrics['cagr']:>6.2f}% {metrics['total_return']:>12.2f}% "
            f"{metrics['max_drawdown']:>9.2f}% ${metrics['final_value']:>11.2f} "
            f"{'YES' if beats_spy else 'no':>9}"
        )

    for start_year in (2015, 2020):
        period_benchmark = calculate_metrics(candidate_returns['SPY Buy & Hold'], start_year)
        period_results = []
        for name in candidate_returns.columns:
            metrics = calculate_metrics(candidate_returns[name], start_year)
            period_results.append((metrics['cagr'], name, metrics))
        print(f"\nWINDOW CHECK FROM {start_year} | SPY CAGR {period_benchmark['cagr']:.2f}%")
        for cagr, name, metrics in sorted(period_results, reverse=True):
            print(
                f"  {name:<31} CAGR {cagr:>6.2f}% | "
                f"Max DD {metrics['max_drawdown']:>7.2f}% | "
                f"Final ${metrics['final_value']:>11.2f}"
            )

    selector_returns, selection_counts = walk_forward_selector(prices, signals, candidate_returns)
    selector_metrics = calculate_metrics(selector_returns, SELECTOR_START_YEAR)
    selector_benchmark = calculate_metrics(candidate_returns['SPY Buy & Hold'], SELECTOR_START_YEAR)
    selector_beats_spy = selector_metrics['final_value'] > selector_benchmark['final_value']
    selector_start_date = selector_metrics['equity'].index[0].date()
    print(f"\nWALK-FORWARD SELECTOR from {selector_start_date}:")
    print("Strategy selection uses the prior 756 trading days; score = CAGR - 0.25 x max drawdown.")
    print(
        f"  Selector       CAGR {selector_metrics['cagr']:>6.2f}% | "
        f"Total {selector_metrics['total_return']:>8.2f}% | "
        f"Max DD {selector_metrics['max_drawdown']:>7.2f}% | "
        f"Final ${selector_metrics['final_value']:>11.2f}"
    )
    print(
        f"  SPY buy-hold   CAGR {selector_benchmark['cagr']:>6.2f}% | "
        f"Total {selector_benchmark['total_return']:>8.2f}% | "
        f"Max DD {selector_benchmark['max_drawdown']:>7.2f}% | "
        f"Final ${selector_benchmark['final_value']:>11.2f}"
    )
    print(f"  Selector beat SPY: {'YES' if selector_beats_spy else 'no'}")
    print("  Most selected strategies:")
    for name, months in selection_counts.head(5).items():
        print(f"    {name}: {months} months")

    selector_equity = selector_metrics['equity']
    benchmark_equity = selector_benchmark['equity']
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(selector_equity, label='V3 walk-forward selector', linewidth=1.6)
    ax.plot(benchmark_equity, label='Dividend-adjusted SPY buy & hold', linewidth=1.6)
    ax.set_title('V3 Walk-Forward Strategy Selection vs SPY')
    ax.set_ylabel('Portfolio value ($)')
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig('backtester_v3_results.png', dpi=120)
    print('Chart saved to backtester_v3_results.png')
    plt.show()


if __name__ == '__main__':
    main()
