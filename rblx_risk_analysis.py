"""
RBLX risk-return analysis
=========================
Compares Roblox (RBLX) with the S&P 500 (via the SPY ETF) using daily returns.

Metrics: annualised return, annualised volatility, Sharpe ratio, beta,
maximum drawdown and 1-day historical Value at Risk (VaR).

How to run
----------
Option A (internet): pip install yfinance pandas numpy matplotlib, then run
    python rblx_risk_analysis.py
Option B (no yfinance): download the historical data for RBLX and SPY from
    Yahoo Finance as CSV, save them as RBLX.csv and SPY.csv next to this file, then run the same command.

Outputs: a printed summary table and rblx_risk_analysis.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TICKER, BENCH = "RBLX", "SPY"
START = "2021-04-01"      # RBLX listed in March 2021
RISK_FREE = 0.04          # assumed annual risk-free rate; change as you see fit
TRADING_DAYS = 252
VAR_LEVEL = 0.05          # 95% VaR


def load_prices() -> pd.DataFrame:
    """Return a DataFrame of adjusted closing prices with columns [TICKER, BENCH]."""
    try:
        import yfinance as yf
        data = yf.download([TICKER, BENCH], start=START, auto_adjust=True, progress=False)["Close"]
    except ImportError:
        frames = {}
        for t in (TICKER, BENCH):
            df = pd.read_csv(f"{t}.csv", parse_dates=["Date"], index_col="Date")
            col = "Adj Close" if "Adj Close" in df.columns else "Close"
            frames[t] = df[col]
        data = pd.DataFrame(frames).loc[START:]
    return data[[TICKER, BENCH]].dropna().sort_index()


def max_drawdown(prices: pd.Series) -> pd.Series:
    """Drawdown series: % fall from the running peak."""
    return prices / prices.cummax() - 1


def summarise(returns: pd.Series, prices: pd.Series, bench_returns: pd.Series) -> dict:
    years = len(returns) / TRADING_DAYS
    # CAGR: the return you would actually have earned, from real start/end prices
    cagr = (prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1
    # Arithmetic average annual return: used for the Sharpe ratio. It ignores
    # volatility drag, so for very volatile stocks it is HIGHER than CAGR.
    ann_ret = returns.mean() * TRADING_DAYS
    ann_vol = returns.std() * np.sqrt(TRADING_DAYS)
    beta = returns.cov(bench_returns) / bench_returns.var()
    return {
        "CAGR (compound return)": cagr,
        "Avg annual return (arith.)": ann_ret,
        "Annualised volatility": ann_vol,
        "Sharpe ratio": (ann_ret - RISK_FREE) / ann_vol,
        "Beta vs S&P 500": beta,
        "Max drawdown": max_drawdown(prices).min(),
        "1-day 95% VaR": -np.percentile(returns, VAR_LEVEL * 100),
    }


def main():
    prices = load_prices()
    returns = prices.pct_change().dropna()

    results = pd.DataFrame({
        TICKER: summarise(returns[TICKER], prices[TICKER], returns[BENCH]),
        BENCH: summarise(returns[BENCH], prices[BENCH], returns[BENCH]),
    })
    print(f"\nPeriod: {prices.index[0].date()} to {prices.index[-1].date()}  ({len(returns)} trading days)\n")
    for metric, row in results.iterrows():
        fmt = (lambda v: f"{v:8.2f}") if metric in ("Sharpe ratio", "Beta vs S&P 500") else (lambda v: f"{v:8.1%}")
        print(f"{metric:<24}" + "".join(fmt(v) for v in row))
    print()

    # Charts
    fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
    (prices / prices.iloc[0] * 100).plot(ax=axes[0])
    axes[0].set_title("Growth of 100 invested"); axes[0].set_ylabel("Value")

    dd = prices.apply(max_drawdown)
    dd.plot(ax=axes[1]); axes[1].set_title("Drawdown from previous peak"); axes[1].set_ylabel("Drawdown")

    (returns.rolling(60).std() * np.sqrt(TRADING_DAYS)).plot(ax=axes[2])
    axes[2].set_title("Rolling 60-day annualised volatility"); axes[2].set_ylabel("Volatility")

    plt.tight_layout()
    plt.savefig("rblx_risk_analysis.png", dpi=150)
    print("Saved chart to rblx_risk_analysis.png")


if __name__ == "__main__":
    main() 
