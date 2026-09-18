import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def backtest_year(symbol, year, transaction_fee=0.001, stop_loss_pct=0.05):
    """Simple backtester for one year."""

    start = f"{year}-01-01"
    end = f"{year}-12-31"
    data = yf.download(symbol, start=start, end=end, progress=False)

    if data is None or getattr(data, 'empty', True):
        return {
            'return': 0.0,
            'drawdown': 0.0,
            'trades': 0,
            'bh_return': 0.0,
            'portfolio': [10000.0],
            'final': 10000.0,
        }

    data = data.copy()

    close_candidates = []
    for col in data.columns:
        if isinstance(col, tuple):
            names = [str(part) for part in col if str(part).strip()]
        else:
            names = [str(col)]

        for name in names:
            if name.lower() == 'close':
                close_candidates.append(col)
            elif name.lower().endswith('close') and 'adj' not in name.lower():
                close_candidates.append(col)

    if not close_candidates:
        numeric_cols = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col])]
        if numeric_cols:
            close_candidates = [numeric_cols[0]]
        else:
            raise ValueError(f"No Close column found for {symbol} in {year}.")

    close_series = data[close_candidates[0]]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]
    if not isinstance(close_series, pd.Series):
        close_series = pd.Series(close_series)

    close_series = pd.to_numeric(close_series, errors='coerce')
    data = pd.DataFrame({'Close': close_series}).dropna().copy()

    if data.empty:
        return {
            'return': 0.0,
            'drawdown': 0.0,
            'trades': 0,
            'bh_return': 0.0,
            'portfolio': [10000.0],
            'final': 10000.0,
        }

    data['MA20'] = data['Close'].rolling(20).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    data['Vol'] = data['Close'].pct_change().rolling(20).std()

    close = data['Close'].to_numpy(dtype=float)
    ma20 = data['MA20'].to_numpy(dtype=float)
    ma50 = data['MA50'].to_numpy(dtype=float)
    ma200 = data['MA200'].to_numpy(dtype=float)
    vol_arr = data['Vol'].to_numpy(dtype=float)

    cash = 10000.0
    shares = 0.0
    entry_price = 0.0
    position = False
    trades = []
    portfolio = []
    cooldown = 0

    for idx, price in enumerate(close):
        ma20_val = ma20[idx]
        ma50_val = ma50[idx]
        ma200_val = ma200[idx]
        vol = vol_arr[idx]

        if np.isnan(ma20_val) or np.isnan(ma50_val) or np.isnan(ma200_val):
            portfolio.append(float(cash))
            continue

        if position and price <= entry_price * (1 - stop_loss_pct):
            cash += shares * price * (1 - transaction_fee)
            trades.append(('SL', float(price)))
            position = False
            shares = 0.0
            cooldown = 10
            portfolio.append(float(cash))
            continue

        if cooldown > 0:
            cooldown -= 1

        if not position:
            trend_ok = ma20_val > ma50_val and price > ma200_val
            if trend_ok and cooldown == 0:
                vol_size = 1.0
                if not np.isnan(vol) and vol > 0:
                    vol_size = float(np.clip(0.015 / vol, 0.4, 1.2))

                if price > 0 and cash > 0:
                    shares = (cash / price) * vol_size
                    cash -= shares * price * (1 + transaction_fee)
                    entry_price = float(price)
                    trades.append(('BUY', float(price)))
                    position = True

        elif position:
            exit_signal = ma20_val < ma50_val or price < ma200_val
            if exit_signal:
                cash += shares * price * (1 - transaction_fee)
                trades.append(('SELL', float(price)))
                position = False
                shares = 0.0
                cooldown = 10

        pv = cash + (shares * price if position else 0.0)
        portfolio.append(float(pv))

    if not portfolio:
        return {
            'return': 0.0,
            'drawdown': 0.0,
            'trades': 0,
            'bh_return': 0.0,
            'portfolio': [10000.0],
            'final': 10000.0,
        }

    final_price = float(close[-1])
    final_cash = cash + (shares * final_price if position else 0.0)
    ret = ((final_cash - 10000.0) / 10000.0) * 100.0

    dd = []
    peak = portfolio[0]
    for pv in portfolio:
        if pv > peak:
            peak = pv
        dd.append(((pv - peak) / peak) * 100.0 if peak else 0.0)

    first_price = float(close[0])
    buy_hold = ((final_price - first_price) / first_price) * 100.0 if first_price else 0.0

    return {
        'return': float(ret),
        'drawdown': float(min(dd) if dd else 0.0),
        'trades': len(trades),
        'bh_return': float(buy_hold),
        'portfolio': portfolio,
        'final': float(final_cash),
    }

def main():
    symbol = 'SPY'
    results = {}
    years = [2017, 2022, 2015, 2021]

    print("Running backtests...\n")
    for year in years:
        print(f"  {year}...", end=" ")
        results[year] = backtest_year(symbol, year)
        print("✓")

    print(f"\n{'='*70}")
    print(f"BACKTESTER: {symbol} | MA 20/50 Crossover | 0.1% Fee | 5% Stop Loss")
    print(f"{'='*70}\n")

    for year in sorted(results.keys()):
        r = results[year]
        print(f"YEAR {year}:")
        print(f"  Strategy Return:    {r['return']:>7.2f}%")
        print(f"  Buy & Hold Return:  {r['bh_return']:>7.2f}%")
        print(f"  Max Drawdown:       {r['drawdown']:>7.2f}%")
        print(f"  Total Trades:       {r['trades']:>7}")
        print(f"  Final Value:        ${r['final']:>7.2f}\n")

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    for idx, year in enumerate(sorted(results.keys())):
        r = results[year]
        row = idx // 2
        col = idx % 2
        ax[row, col].plot(r['portfolio'], color='blue', linewidth=2)
        ax[row, col].set_title(f"{year}: {r['return']:.1f}% (DD {r['drawdown']:.1f}%)")
        ax[row, col].grid(alpha=0.3)
        ax[row, col].set_ylabel('Portfolio ($)')

    plt.suptitle('SPY Backtester Results', fontsize=14)
    plt.tight_layout()
    plt.savefig('backtester_results.png', dpi=100)
    print("✓ Chart saved")
    plt.show()


if __name__ == "__main__":
    main()
