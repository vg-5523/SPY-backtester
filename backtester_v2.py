import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _empty_result():
    return {
        'return': 0.0,
        'drawdown': 0.0,
        'trades': 0,
        'bh_return': 0.0,
        'portfolio': [10000.0],
        'final': 10000.0,
    }


def backtest_year(
    symbol,
    year,
    transaction_fee=0.001,
    stop_loss_pct=0.05,
    strategy='advanced',
    volatility_target=0.12,
):
    """Compare one strategy over a calendar year, with a prior-year warmup."""
    if strategy not in {'baseline', 'advanced'}:
        raise ValueError("strategy must be 'baseline' or 'advanced'.")
    if volatility_target <= 0:
        raise ValueError("volatility_target must be greater than zero.")

    start = f"{year - 1}-01-01"
    end = f"{year + 1}-01-01"
    data = yf.download(symbol, start=start, end=end, progress=False)
    if data is None or getattr(data, 'empty', True):
        return _empty_result()

    close_candidates = []
    for col in data.columns:
        names = [str(part) for part in col if str(part).strip()] if isinstance(col, tuple) else [str(col)]
        if any(name.lower() == 'close' for name in names):
            close_candidates.append(col)
    if not close_candidates:
        raise ValueError(f"No Close column found for {symbol} in {year}.")

    close_series = data[close_candidates[0]]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]
    data = pd.DataFrame({'Close': pd.to_numeric(close_series, errors='coerce')}).dropna()
    if data.empty:
        return _empty_result()

    data['MA20'] = data['Close'].rolling(20).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    data['DailyVol'] = data['Close'].pct_change().rolling(20).std()
    data['AnnualVol'] = data['DailyVol'] * np.sqrt(252)
    data['Momentum126'] = data['Close'].pct_change(126)

    year_indices = np.flatnonzero(data.index.year == year)
    if len(year_indices) == 0:
        return _empty_result()

    close = data['Close'].to_numpy(dtype=float)
    ma20 = data['MA20'].to_numpy(dtype=float)
    ma50 = data['MA50'].to_numpy(dtype=float)
    ma200 = data['MA200'].to_numpy(dtype=float)
    daily_vol = data['DailyVol'].to_numpy(dtype=float)
    annual_vol = data['AnnualVol'].to_numpy(dtype=float)
    momentum = data['Momentum126'].to_numpy(dtype=float)

    cash = 10000.0
    shares = 0.0
    entry_price = 0.0
    trades = 0
    portfolio = []
    cooldown = 0

    for idx in year_indices:
        price = float(close[idx])
        signal_idx = idx - 1
        exited_today = False
        if cooldown > 0:
            cooldown -= 1

        indicators_ready = (
            signal_idx >= 0
            and not np.isnan(ma20[signal_idx])
            and not np.isnan(ma50[signal_idx])
            and not np.isnan(ma200[signal_idx])
        )

        if indicators_ready and shares > 0:
            prior_close = close[signal_idx]
            if strategy == 'baseline':
                exit_signal = (
                    prior_close <= entry_price * (1 - stop_loss_pct)
                    or ma20[signal_idx] < ma50[signal_idx]
                    or prior_close < ma200[signal_idx]
                )
            else:
                exit_signal = prior_close < ma200[signal_idx] or momentum[signal_idx] <= 0

            if exit_signal:
                cash += shares * price * (1 - transaction_fee)
                shares = 0.0
                trades += 1
                cooldown = 10
                exited_today = True

        if indicators_ready and shares == 0 and not exited_today and cooldown == 0:
            if strategy == 'baseline':
                entry_signal = ma20[signal_idx] > ma50[signal_idx] and close[signal_idx] > ma200[signal_idx]
                weight = 1.0
                if daily_vol[signal_idx] > 0:
                    weight = float(np.clip(0.015 / daily_vol[signal_idx], 0.4, 1.0))
            else:
                entry_signal = (
                    close[signal_idx] > ma200[signal_idx]
                    and ma50[signal_idx] > ma200[signal_idx]
                    and momentum[signal_idx] > 0
                )
                volatility = annual_vol[signal_idx]
                weight = min(1.0, volatility_target / volatility) if volatility > 0 else 1.0

            if entry_signal and price > 0 and cash > 0:
                equity = cash
                shares = equity * weight / (price * (1 + transaction_fee))
                cash -= shares * price * (1 + transaction_fee)
                entry_price = price
                trades += 1

        portfolio.append(float(cash + shares * price))

    if not portfolio:
        return _empty_result()

    final_cash = float(portfolio[-1])
    ret = ((final_cash - 10000.0) / 10000.0) * 100.0
    peak = portfolio[0]
    drawdowns = []
    for value in portfolio:
        peak = max(peak, value)
        drawdowns.append(((value - peak) / peak) * 100.0 if peak else 0.0)

    first_price = float(close[year_indices[0]])
    final_price = float(close[year_indices[-1]])
    buy_hold = ((final_price - first_price) / first_price) * 100.0 if first_price else 0.0
    return {
        'return': float(ret),
        'drawdown': float(min(drawdowns) if drawdowns else 0.0),
        'trades': trades,
        'bh_return': float(buy_hold),
        'portfolio': portfolio,
        'final': final_cash,
    }


def backtest_rotation(
    start_year=2005,
    transaction_fee=0.001,
    max_holdings=2,
    require_spy_trend=True,
):
    """Backtest an unleveraged monthly ETF rotation against total-return SPY."""
    if max_holdings < 1:
        raise ValueError('max_holdings must be at least one.')

    risk_assets = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD']
    defensive_asset = 'SHY'
    symbols = risk_assets + [defensive_asset]
    data = yf.download(
        symbols,
        start='2004-01-01',
        auto_adjust=True,
        progress=False,
        group_by='ticker',
    )
    if data is None or data.empty:
        raise ValueError('No adjusted ETF price data was downloaded.')

    closes = {}
    for symbol in symbols:
        close_column = (symbol, 'Close')
        if close_column not in data.columns:
            raise ValueError(f"No adjusted Close column found for {symbol}.")
        closes[symbol] = data[close_column]
    prices = pd.DataFrame(closes).sort_index().ffill().dropna(subset=['SPY'])
    sma200 = prices.rolling(200).mean()
    momentum_6m = prices.pct_change(126)
    momentum_12m = prices.pct_change(252)
    momentum_score = (momentum_6m + momentum_12m) / 2

    decisions = pd.DataFrame(np.nan, index=prices.index, columns=symbols)
    month_ends = prices.groupby(prices.index.to_period('M')).tail(1).index
    for date in month_ends:
        weights = pd.Series(0.0, index=symbols)
        if require_spy_trend and prices.at[date, 'SPY'] <= sma200.at[date, 'SPY']:
            weights[defensive_asset] = 1.0
        else:
            eligible = [
                symbol for symbol in risk_assets
                if prices.at[date, symbol] > sma200.at[date, symbol]
                and momentum_6m.at[date, symbol] > 0
                and momentum_12m.at[date, symbol] > 0
            ]
            ranked = momentum_score.loc[date, eligible].dropna().nlargest(max_holdings)
            if ranked.empty:
                weights[defensive_asset] = 1.0
            else:
                weights.loc[ranked.index] = 1.0 / len(ranked)
        decisions.loc[date] = weights

    execution_weights = decisions.ffill().shift(1).fillna(0.0)
    holding_weights = execution_weights.shift(1).fillna(0.0)
    asset_returns = prices.pct_change().fillna(0.0)
    turnover = execution_weights.diff().abs().sum(axis=1).fillna(0.0)
    strategy_returns = (holding_weights * asset_returns).sum(axis=1) - turnover * transaction_fee
    benchmark_returns = asset_returns['SPY'].copy()

    first_test_idx = np.flatnonzero(prices.index.year >= start_year)
    if len(first_test_idx) == 0:
        raise ValueError(f"No price data found from {start_year} onward.")
    first_test_date = prices.index[first_test_idx[0]]
    benchmark_returns.loc[first_test_date] -= transaction_fee
    strategy_returns = strategy_returns.loc[first_test_date:]
    benchmark_returns = benchmark_returns.loc[first_test_date:]
    strategy_equity = 10000.0 * (1 + strategy_returns).cumprod()
    benchmark_equity = 10000.0 * (1 + benchmark_returns).cumprod()

    def summarize(equity, daily_returns):
        years = len(daily_returns) / 252
        total_return = (equity.iloc[-1] / 10000.0 - 1) * 100
        cagr = ((equity.iloc[-1] / 10000.0) ** (1 / years) - 1) * 100
        drawdown = ((equity / equity.cummax()) - 1).min() * 100
        return {
            'total_return': float(total_return),
            'cagr': float(cagr),
            'drawdown': float(drawdown),
            'final': float(equity.iloc[-1]),
        }

    return {
        'strategy': summarize(strategy_equity, strategy_returns),
        'buy_hold': summarize(benchmark_equity, benchmark_returns),
        'strategy_equity': strategy_equity,
        'buy_hold_equity': benchmark_equity,
        'rebalances': int((turnover.loc[first_test_date:] > 0).sum()),
        'start_date': first_test_date,
        'end_date': prices.index[-1],
    }


def main():
    symbol = 'SPY'
    results = {}
    years = [2017, 2022, 2015, 2021]

    print("Running V2 strategy comparisons...\n")
    for year in years:
        print(f"  {year}...", end=" ")
        results[year] = {
            'baseline': backtest_year(symbol, year, strategy='baseline'),
            'advanced_12': backtest_year(symbol, year, strategy='advanced', volatility_target=0.12),
            'advanced_20': backtest_year(symbol, year, strategy='advanced', volatility_target=0.20),
        }
        print("done")

    print(f"\n{'='*86}")
    print(f"BACKTESTER V2: {symbol} | 0.1% Fee | Next-session close execution")
    print("Baseline: MA20/MA50 + SMA200 | Advanced: SMA50/SMA200 + 126-day momentum")
    print("Advanced sizing variants: 12% and 20% volatility targets, both capped at 100% invested")
    print(f"{'='*86}\n")

    for year in sorted(results.keys()):
        print(f"YEAR {year}:")
        for name in ('baseline', 'advanced_12', 'advanced_20'):
            result = results[year][name]
            print(
                f"  {name.replace('_', ' ').title():<11} Return {result['return']:>7.2f}% | "
                f"Drawdown {result['drawdown']:>7.2f}% | Trades {result['trades']:>3} | "
                f"Final ${result['final']:>9.2f}"
            )
        print(f"  Buy & Hold Return: {results[year]['advanced_12']['bh_return']:>7.2f}%\n")

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    for idx, year in enumerate(sorted(results.keys())):
        row = idx // 2
        col = idx % 2
        baseline = results[year]['baseline']
        advanced_12 = results[year]['advanced_12']
        advanced_20 = results[year]['advanced_20']
        ax[row, col].plot(baseline['portfolio'], label='Baseline', linewidth=1.5)
        ax[row, col].plot(advanced_12['portfolio'], label='Advanced 12%', linewidth=1.5)
        ax[row, col].plot(advanced_20['portfolio'], label='Advanced 20%', linewidth=1.5)
        ax[row, col].set_title(
            f"{year}: 12% target {advanced_12['return']:.1f}% | 20% target {advanced_20['return']:.1f}%"
        )
        ax[row, col].grid(alpha=0.3)
        ax[row, col].set_ylabel('Portfolio ($)')
        ax[row, col].legend()

    plt.suptitle('SPY V2 Strategy Comparison', fontsize=14)
    plt.tight_layout()
    plt.savefig('backtester_v2_results.png', dpi=100)
    print("Chart saved to backtester_v2_results.png")
    plt.show()

    balanced = backtest_rotation(max_holdings=2, require_spy_trend=True)
    growth = backtest_rotation(max_holdings=1, require_spy_trend=False)
    recent_growth = backtest_rotation(start_year=2015, max_holdings=1, require_spy_trend=False)
    print(f"\nMULTI-ETF ROTATION: {balanced['start_date'].date()} to {balanced['end_date'].date()}")
    print("Universe: SPY, QQQ, IWM, TLT, GLD; SHY defensive | Monthly rebalance | No leverage")
    for label, result in (
        ('Balanced (2 assets)', balanced['strategy']),
        ('Growth (1 asset)', growth['strategy']),
        ('SPY buy & hold', balanced['buy_hold']),
    ):
        print(
            f"  {label:<20} Total {result['total_return']:>8.2f}% | "
            f"CAGR {result['cagr']:>6.2f}% | Max DD {result['drawdown']:>7.2f}% | "
            f"Final ${result['final']:>12.2f}"
        )
    print(f"  Rebalances: balanced {balanced['rebalances']}, growth {growth['rebalances']}")
    print(f"\nRECENT-PERIOD CHECK: {recent_growth['start_date'].date()} to {recent_growth['end_date'].date()}")
    for label, result in (
        ('Growth (1 asset)', recent_growth['strategy']),
        ('SPY buy & hold', recent_growth['buy_hold']),
    ):
        print(
            f"  {label:<20} Total {result['total_return']:>8.2f}% | "
            f"CAGR {result['cagr']:>6.2f}% | Max DD {result['drawdown']:>7.2f}% | "
            f"Final ${result['final']:>12.2f}"
        )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(balanced['strategy_equity'], label='Balanced rotation', linewidth=1.5)
    ax.plot(growth['strategy_equity'], label='Growth rotation', linewidth=1.5)
    ax.plot(balanced['buy_hold_equity'], label='SPY buy & hold', linewidth=1.5)
    ax.set_title('V2 Multi-ETF Rotation vs SPY Buy & Hold')
    ax.set_ylabel('Portfolio value ($)')
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig('backtester_v2_rotation.png', dpi=120)
    print("Chart saved to backtester_v2_rotation.png")
    plt.show()


if __name__ == "__main__":
    main()
