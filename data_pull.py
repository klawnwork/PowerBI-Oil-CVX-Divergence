"""
Oil-Equity Divergence Tracker - Master Data Pull
=================================================
This script pulls all market data needed for the Power BI dashboard project.
Run this once to generate all CSV files. Re-run only when you want to refresh data.

Output files:
  1. market_data.csv            - All raw prices and normalized values (2021-present)
  2. rolling_correlations.csv   - Rolling correlation between CVX and WTI at multiple windows
  3. spread_analysis.csv        - Divergence spreads and z-scores
  4. events.csv                 - Key geopolitical/market events for annotation overlay
  5. historical_context.csv     - CVX vs WTI back to 2010 for long-term context

Author: Kyle (BetterBlood Technologies LLC)
Project: Oil-Equity Divergence Tracker - Power BI Portfolio Project
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# CONFIGURATION - Change these if needed
# ============================================================
START_DATE = "2021-03-07"
END_DATE = datetime.today().strftime("%Y-%m-%d")

TICKERS = {
    # Core analysis
    "CVX": "Chevron",
    "CL=F": "WTI Crude Oil",
    
    # Sector comparisons
    "XOM": "ExxonMobil",
    "COP": "ConocoPhillips",
    "OXY": "Occidental Petroleum",
    "XLE": "Energy Select ETF",
    
    # Macro indicators
    "DX-Y.NYB": "US Dollar Index (DXY)",
    "SPY": "S&P 500 ETF",
    "UNG": "US Natural Gas Fund",
    "BZ=F": "Brent Crude Oil",
    "^TNX": "10Y Treasury Yield",
}

# Clean column name mapping (no special characters)
TICKER_TO_COL = {
    "CVX": "CVX",
    "CL=F": "WTI",
    "XOM": "XOM",
    "COP": "COP",
    "OXY": "OXY",
    "XLE": "XLE",
    "DX-Y.NYB": "DXY",
    "SPY": "SPY",
    "UNG": "NatGas",
    "BZ=F": "Brent",
    "^TNX": "Treasury10Y",
}

# ============================================================
# FILE 1: MARKET DATA (raw prices + normalized + spreads)
# ============================================================
print("=" * 60)
print("PULLING MARKET DATA")
print("=" * 60)

frames = {}
for ticker, name in TICKERS.items():
    col_name = TICKER_TO_COL[ticker]
    print(f"  Downloading {name} ({ticker})...")
    try:
        data = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
        if len(data) > 0:
            close = data[["Close"]].copy()
            close.columns = [f"{col_name}_Close"]
            frames[col_name] = close
            print(f"    -> {len(close)} rows")
        else:
            print(f"    -> WARNING: No data returned")
    except Exception as e:
        print(f"    -> ERROR: {e}")

# Merge all on date using inner join (only dates where ALL tickers have data)
print("\nMerging datasets...")
combined = frames["CVX"]
for col_name, df in frames.items():
    if col_name != "CVX":
        combined = combined.join(df, how="inner")

combined.index.name = "Date"
combined = combined.reset_index()
print(f"  Combined dataset: {len(combined)} rows, {len(combined.columns)} columns")

# Normalize all price columns to 100 at start
print("Normalizing to base 100...")
price_cols = [c for c in combined.columns if c.endswith("_Close")]
for col in price_cols:
    norm_col = col.replace("_Close", "_Norm")
    first_val = combined[col].iloc[0]
    if first_val != 0 and not pd.isna(first_val):
        combined[norm_col] = combined[col] / first_val * 100
    else:
        combined[norm_col] = np.nan

# Calculate key spreads
print("Calculating spreads...")
combined["Spread_CVX_vs_WTI"] = combined["CVX_Norm"] - combined["WTI_Norm"]
combined["Spread_CVX_vs_XLE"] = combined["CVX_Norm"] - combined["XLE_Norm"]
combined["Spread_CVX_vs_XOM"] = combined["CVX_Norm"] - combined["XOM_Norm"]
combined["Spread_XLE_vs_WTI"] = combined["XLE_Norm"] - combined["WTI_Norm"]
combined["Spread_CVX_vs_SPY"] = combined["CVX_Norm"] - combined["SPY_Norm"]

# WTI vs Brent spread (in raw dollars - useful for geopolitical analysis)
combined["WTI_Brent_Spread"] = combined["WTI_Close"] - combined["Brent_Close"]

# Year, Month, Quarter columns for Power BI slicing
combined["Year"] = pd.to_datetime(combined["Date"]).dt.year
combined["Month"] = pd.to_datetime(combined["Date"]).dt.month
combined["Quarter"] = pd.to_datetime(combined["Date"]).dt.quarter
combined["YearMonth"] = pd.to_datetime(combined["Date"]).dt.to_period("M").astype(str)
combined["DayOfWeek"] = pd.to_datetime(combined["Date"]).dt.day_name()

# Export
combined.to_csv("market_data.csv", index=False)
print(f"\n-> Exported market_data.csv ({len(combined)} rows, {len(combined.columns)} columns)")

# ============================================================
# FILE 2: ROLLING CORRELATIONS
# ============================================================
print("\n" + "=" * 60)
print("CALCULATING ROLLING CORRELATIONS")
print("=" * 60)

# Calculate daily returns first (correlation of returns is more meaningful than correlation of levels)
returns = pd.DataFrame()
returns["Date"] = combined["Date"]
for col in price_cols:
    ret_col = col.replace("_Close", "_Return")
    returns[ret_col] = combined[col].pct_change()

# Rolling correlations between CVX and WTI at different windows
corr_df = pd.DataFrame()
corr_df["Date"] = combined["Date"]

for window in [30, 60, 90, 180]:
    col_name = f"Corr_CVX_WTI_{window}d"
    corr_df[col_name] = returns["CVX_Return"].rolling(window=window).corr(returns["WTI_Return"])
    
    col_name2 = f"Corr_CVX_SPY_{window}d"
    corr_df[col_name2] = returns["CVX_Return"].rolling(window=window).corr(returns["SPY_Return"])
    
    col_name3 = f"Corr_CVX_XLE_{window}d"
    corr_df[col_name3] = returns["CVX_Return"].rolling(window=window).corr(returns["XLE_Return"])

# Also add CVX vs DXY correlation (oil stocks often inversely correlated with strong dollar)
for window in [30, 90]:
    col_name = f"Corr_CVX_DXY_{window}d"
    corr_df[col_name] = returns["CVX_Return"].rolling(window=window).corr(returns["DXY_Return"])
    
    col_name2 = f"Corr_WTI_DXY_{window}d"
    corr_df[col_name2] = returns["WTI_Return"].rolling(window=window).corr(returns["DXY_Return"])

corr_df.to_csv("rolling_correlations.csv", index=False)
print(f"-> Exported rolling_correlations.csv ({len(corr_df)} rows)")

# ============================================================
# FILE 3: SPREAD ANALYSIS (z-scores for identifying extremes)
# ============================================================
print("\n" + "=" * 60)
print("CALCULATING SPREAD ANALYSIS")
print("=" * 60)

spread_df = pd.DataFrame()
spread_df["Date"] = combined["Date"]
spread_df["Spread_CVX_WTI"] = combined["Spread_CVX_vs_WTI"]

# Rolling mean and std of the spread
for window in [30, 90, 180]:
    mean_col = f"Spread_Mean_{window}d"
    std_col = f"Spread_Std_{window}d"
    zscore_col = f"Spread_ZScore_{window}d"
    
    spread_df[mean_col] = spread_df["Spread_CVX_WTI"].rolling(window=window).mean()
    spread_df[std_col] = spread_df["Spread_CVX_WTI"].rolling(window=window).std()
    spread_df[zscore_col] = (
        (spread_df["Spread_CVX_WTI"] - spread_df[mean_col]) / spread_df[std_col]
    )

# Flag extreme divergence periods (z-score > 2 or < -2)
spread_df["Extreme_Divergence"] = spread_df["Spread_ZScore_90d"].apply(
    lambda x: "CVX Outperforming" if x > 2 else ("Oil Outperforming" if x < -2 else "Normal")
)

spread_df.to_csv("spread_analysis.csv", index=False)
print(f"-> Exported spread_analysis.csv ({len(spread_df)} rows)")

# ============================================================
# FILE 4: KEY EVENTS FOR ANNOTATION
# ============================================================
print("\n" + "=" * 60)
print("CREATING EVENTS TIMELINE")
print("=" * 60)

events = pd.DataFrame({
    "Date": [
        "2021-03-07", "2022-02-24", "2022-03-08", "2022-06-08",
        "2022-10-05", "2022-12-05", "2023-04-02", "2023-06-04",
        "2023-10-07", "2023-10-23", "2024-01-11", "2024-03-01",
        "2024-06-02", "2024-09-12", "2024-11-05", "2024-12-05",
        "2025-01-20", "2025-04-02", "2025-09-15",
    ],
    "Event": [
        "Dashboard Start Date",
        "Russia Invades Ukraine",
        "WTI Hits $130 - War Premium Peak",
        "WTI Peaks Above $120",
        "OPEC+ Announces 2M bbl/day Cut",
        "EU Russian Oil Price Cap ($60)",
        "OPEC+ Surprise Cut 1.16M bbl/day",
        "OPEC+ Saudi Voluntary 1M bbl/day Cut",
        "Hamas Attack on Israel",
        "CVX Announces Hess Acquisition ($53B)",
        "Houthis Escalate Red Sea Attacks",
        "OPEC+ Extends Cuts Through Q2 2024",
        "OPEC+ Plans Gradual Output Increase",
        "CVX-Hess Arbitration Ruling Expected",
        "US Presidential Election",
        "OPEC+ Delays Output Increase to Apr 2025",
        "Trump Inauguration / Energy Policy Shift",
        "Trump Tariff Announcements",
        "OPEC+ Gradual Unwinding Begins",
    ],
    "Category": [
        "Reference",
        "Geopolitical", "Oil Market", "Oil Market",
        "OPEC", "Geopolitical", "OPEC", "OPEC",
        "Geopolitical", "CVX Specific", "Geopolitical", "OPEC",
        "OPEC", "CVX Specific", "Geopolitical", "OPEC",
        "Geopolitical", "Geopolitical", "OPEC",
    ],
    "Impact": [
        "Neutral",
        "Oil Bullish", "Oil Bullish", "Oil Bullish",
        "Oil Bullish", "Oil Bearish", "Oil Bullish", "Oil Bullish",
        "Oil Bullish", "CVX Bullish", "Oil Bullish", "Oil Bullish",
        "Oil Bearish", "CVX Specific", "Mixed", "Oil Bullish",
        "Oil Bullish", "Oil Bearish", "Oil Bearish",
    ],
})

events.to_csv("events.csv", index=False)
print(f"-> Exported events.csv ({len(events)} events)")

# ============================================================
# FILE 5: HISTORICAL CONTEXT (CVX vs WTI back to 2010)
# ============================================================
print("\n" + "=" * 60)
print("PULLING HISTORICAL CONTEXT DATA")
print("=" * 60)

HIST_START = "2010-01-01"

hist_frames = {}
for ticker, col_name in [("CVX", "CVX"), ("CL=F", "WTI")]:
    print(f"  Downloading {col_name} from {HIST_START}...")
    try:
        data = yf.download(ticker, start=HIST_START, end=END_DATE, progress=False)
        if len(data) > 0:
            close = data[["Close"]].copy()
            close.columns = [f"{col_name}_Close"]
            hist_frames[col_name] = close
            print(f"    -> {len(close)} rows")
        else:
            print(f"    -> WARNING: No data returned")
    except Exception as e:
        print(f"    -> ERROR: {e}")

# Merge CVX and WTI on date
hist = hist_frames["CVX"].join(hist_frames["WTI"], how="inner")
hist.index.name = "Date"
hist = hist.reset_index()
print(f"  Historical dataset: {len(hist)} rows")

# Normalize to 100 at start
hist["CVX_Norm"] = hist["CVX_Close"] / hist["CVX_Close"].iloc[0] * 100
hist["WTI_Norm"] = hist["WTI_Close"] / hist["WTI_Close"].iloc[0] * 100

# Spread (normalized)
hist["Spread_CVX_WTI"] = hist["CVX_Norm"] - hist["WTI_Norm"]

# Daily returns for correlation calculation
hist["CVX_Return"] = hist["CVX_Close"].pct_change()
hist["WTI_Return"] = hist["WTI_Close"].pct_change()

# Rolling 90d and 180d correlation
hist["Corr_CVX_WTI_90d"] = hist["CVX_Return"].rolling(window=90).corr(hist["WTI_Return"])
hist["Corr_CVX_WTI_180d"] = hist["CVX_Return"].rolling(window=180).corr(hist["WTI_Return"])

# Rolling spread z-score (90d)
hist["Spread_Mean_90d"] = hist["Spread_CVX_WTI"].rolling(window=90).mean()
hist["Spread_Std_90d"] = hist["Spread_CVX_WTI"].rolling(window=90).std()
hist["Spread_ZScore_90d"] = (
    (hist["Spread_CVX_WTI"] - hist["Spread_Mean_90d"]) / hist["Spread_Std_90d"]
)

# Year column for slicing
hist["Year"] = pd.to_datetime(hist["Date"]).dt.year

# Drop intermediate columns not needed in Power BI
hist_export = hist[[
    "Date", "CVX_Close", "WTI_Close", "CVX_Norm", "WTI_Norm",
    "Spread_CVX_WTI", "Corr_CVX_WTI_90d", "Corr_CVX_WTI_180d",
    "Spread_ZScore_90d", "Year"
]].copy()

hist_export.to_csv("historical_context.csv", index=False)
print(f"-> Exported historical_context.csv ({len(hist_export)} rows)")

# ============================================================
# DATA VALIDATION
# ============================================================
print("\n" + "=" * 60)
print("DATA VALIDATION")
print("=" * 60)

for name, df in [("market_data", combined), ("rolling_correlations", corr_df),
                  ("spread_analysis", spread_df), ("historical_context", hist_export)]:
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    print(f"\n  {name}: {len(df)} rows, {len(df.columns)} columns")
    if len(null_cols) > 0:
        print(f"    Columns with NaN (expected for rolling windows):")
        for col, count in null_cols.items():
            print(f"      {col}: {count} nulls ({count/len(df)*100:.1f}%)")
    else:
        print(f"    No null values")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("ALL FILES EXPORTED SUCCESSFULLY")
print("=" * 60)
print(f"""
Files created:
  1. market_data.csv           - {len(combined)} rows, {len(combined.columns)} columns
  2. rolling_correlations.csv  - {len(corr_df)} rows (30/60/90/180 day windows)
  3. spread_analysis.csv       - {len(spread_df)} rows (with z-scores)
  4. events.csv                - {len(events)} key events for annotations
  5. historical_context.csv    - {len(hist_export)} rows (2010-present, CVX vs WTI only)

Import files 1-4 into Power BI using Get Data -> Text/CSV.
The Date column links market_data, rolling_correlations, spread_analysis, and events.

Import historical_context.csv as a STANDALONE table with NO relationships
to the other tables. It uses its own date range and normalization baseline.
""")