


"""
Download historical market data (Yahoo Finance via yfinance) and save to CSV.

Edit the CONFIG section at the top to choose:
- ticker(s)
- interval (time frequency)
- start/end dates
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# -----------------------------
# CONFIG (edit these)
# -----------------------------

# Pick ONE ticker (or set TICKERS list below).
# Examples (comment/uncomment):
# TICKER = "AAPL"   # Apple
# TICKER = "MSFT"   # Microsoft
# TICKER = "NVDA"   # NVIDIA
# TICKER = "TSLA"   # Tesla
# TICKER = "SAP.DE" # SAP (XETRA / Germany)
TICKER = "AAPL"

# If you want multiple tickers, fill this list and set USE_MULTIPLE_TICKERS = True.
# Examples:
# TICKERS = ["AAPL", "MSFT", "NVDA"]
TICKERS = ["AAPL", "MSFT"]
USE_MULTIPLE_TICKERS = False

# Time frequency (Yahoo Finance intervals supported by yfinance include:
# "1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"
# Note: intraday intervals typically have lookback limits on Yahoo (e.g., 1m is very limited).
INTERVAL = "1h"

# Date range:
# Option A) explicit ISO dates (YYYY-MM-DD)
START_DATE = None  # e.g. "2025-12-20"
END_DATE = None    # e.g. "2025-12-27"
# Option B) rolling window (used if START_DATE or END_DATE is None)
ROLLING_DAYS = 20

# Output path (relative to repo root)
OUTPUT_CSV = Path("data/historical_prices.csv")

# -----------------------------
# Logic
# -----------------------------


def _compute_date_range() -> tuple[str, str]:
    """
    Returns (start, end) as YYYY-MM-DD strings.

    yfinance expects end to be exclusive for many intervals, so we provide an end date
    that is "today + 1 day" to safely include the most recent day.
    """
    if START_DATE and END_DATE:
        start = datetime.strptime(START_DATE, "%Y-%m-%d")
        end = datetime.strptime(END_DATE, "%Y-%m-%d")
    else:
        end = datetime.now()
        start = end - timedelta(days=ROLLING_DAYS)

    # Make end exclusive-safe: add one day
    end_excl = end + timedelta(days=1)

    return start.strftime("%Y-%m-%d"), end_excl.strftime("%Y-%m-%d")


def download() -> pd.DataFrame:
    start_str, end_str = _compute_date_range()

    tickers = TICKERS if USE_MULTIPLE_TICKERS else [TICKER]

    # yfinance returns:
    # - Single ticker: columns like Open/High/Low/Close/Adj Close/Volume
    # - Multiple tickers: a multi-index column with (Field, Ticker) or (Ticker, Field)
    data = yf.download(
        tickers=tickers,
        start=start_str,
        end=end_str,
        interval=INTERVAL,
        auto_adjust=False,
        group_by="column",
        progress=False,
    )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_CSV)
    return data


if __name__ == "__main__":
    df = download()
    print(f"Saved {len(df):,} rows to {OUTPUT_CSV}")
    if len(df) > 0:
        print(f"Range: {df.index.min()}  →  {df.index.max()}")
        print(f"Columns: {list(df.columns)[:10]}{' ...' if len(df.columns) > 10 else ''}")