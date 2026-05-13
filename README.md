# Oil-Equity Divergence Tracker

A Power BI dashboard investigating why Chevron (CVX) failed to reprice with crude oil during the 2026 Iran War, despite repricing in lockstep during the 2022 Russia/Ukraine conflict.


**Author:** Kyle Lawn

**Tools:** Python (yfinance, pandas, numpy), Power BI Desktop, DAX

**Data range:** March 7, 2021 – March 6, 2026

**Data source:** Yahoo Finance via yfinance

---

<img width="1273" height="736" alt="image" src="https://github.com/user-attachments/assets/f8f90a91-b74f-4fff-b348-31768479404c" />



---

## The Question

During the first week of the Iran War (Feb 27 – Mar 6, 2026), WTI crude oil surged 35.6%. Chevron — the second-largest integrated U.S. oil major — moved just 1.7%.

This was a sharp departure from the 2022 Russia/Ukraine conflict, when CVX captured 84.8% of WTI's move during a comparable first-week window.

The dashboard investigates: **Why did CVX fail to reprice this time?**

---

## Key Findings

**1. The muted equity response was sector-wide, not CVX-specific.**
XOM, COP, OXY, and the XLE energy ETF all remained near flat while WTI surged. This is consistent with the market treating the oil spike as a temporary geopolitical risk premium rather than a sustained earnings tailwind.

**2. CVX's relationship with oil is regime-dependent, not broken.**
Rolling 90-day correlation between CVX and WTI has fluctuated between roughly 0.2 and 0.7 since 2010, with no sustained directional trend. The relationship is variable rather than structurally broken.

**3. CVX's normalized outperformance of WTI is structural.**
Since 2010, CVX has roughly quintupled on a normalized basis while WTI sits only marginally above its 2010 level. This reflects equity compounding through earnings, dividends, and buybacks — mechanics that commodity prices do not capture.

**4. The CVX-WTI spread is mean-reverting but increasingly stretched.**
The spread has trended positive since mid-2022 and reached a multi-year high in January/February 2026 as WTI gained modestly while CVX spiked sharply higher.

---

## Dashboard Structure

The dashboard consists of 8 pages organized as foundation → context → investigation:

**Foundation pages** (establish the relationship and current state):

1. **Executive Summary** — Current KPIs, hero chart, thesis statement
2. **CVX vs Oil Divergence** — Detailed view of the CVX-WTI spread over time
3. **Sector Comparison** — How CVX compares to XOM, COP, OXY, XLE
4. **Macro Context** — CVX vs DXY (dollar), SPY (broad market), natural gas, and 10Y Treasury
5. **Correlations** — Rolling correlations across multiple windows and reference assets

**Context page** (long-term perspective):

6. **Historical Context** — CVX vs WTI back to 2010 with rolling correlations and z-score

**Investigation pages** (the analytical centerpiece):

7. **Event Comparison** — Side-by-side comparison of the 2022 Russia/Ukraine and 2026 Iran/Hormuz crises, with rebased price action and capture rate metrics
8. **Anomaly Deep Dive** — Z-score timeline, sector peer behavior during the event week, and pre-event correlation breakdown

---

## Methodology

**Data acquisition** is handled by a single Python script (`data_pull.py`) that downloads daily price data from Yahoo Finance, normalizes all assets to a base value of 100, calculates spreads, computes rolling correlations and z-scores, and exports four CSV files for Power BI consumption.

**Normalization approach:** All assets are normalized to 100 at the start date (March 7, 2021 for the main analysis, January 1, 2010 for the historical context). This allows percentage performance to be compared directly across assets with very different price scales.

**Spread calculation:** CVX_Norm minus WTI_Norm. A positive spread means CVX has outperformed WTI since the baseline date.

**Z-score calculation:** Measures how far the current spread is from its 90-day rolling average, scaled by its 90-day rolling standard deviation. Readings beyond ±2 indicate statistically extreme divergence relative to recent history.

**Rolling correlations** are computed on daily *returns* (percentage changes) rather than raw prices. This is the standard approach because correlation of price levels would be misleading when both series have upward trends.

**Event window rebasing:** For the Event Comparison page, both CVX and WTI are independently rebased to 100 on the event start date, enabling direct visual comparison of percentage moves during each crisis.

---

## Technical Implementation

**Python pipeline** (`data_pull.py`):

- Downloads price data for 11 tickers via yfinance
- Inner-joins all series on date (only days where every asset has data)
- Computes normalized values, spreads, rolling returns, rolling correlations, and z-scores
- Outputs 4 CSV files with a built-in validation step that reports null counts per column

**Power BI data model:**

- 4 tables imported: `market_data`, `rolling_correlations`, `spread_analysis`, `historical_context`
- The first three are related on Date with many-to-one cardinality
- `historical_context` is standalone with no relationships — uses a different baseline date

**DAX measures** were used to:

- Pull latest-value KPIs (current CVX price, current spread, current z-score)
- Calculate YTD returns for CVX and WTI
- Translate z-score values into plain-English labels via conditional logic
- Rebase CVX and WTI to 100 at event start dates for the Event Comparison page
- Calculate the CVX-to-WTI capture rate during each event window

**Visual design:**

- Consistent color palette across all pages: CVX `#1565C0`, WTI `#E65100`, with distinct hues for sector peers
- Conditional formatting on z-score cards based on threshold rules
- Constant lines at meaningful thresholds (Y=100 baseline, ±1 z-score bands)
- All calculations done in Python or DAX measures, no calculated columns in the data model

---

## Limitations & Open Questions

This dashboard documents what happened during the Iran/Hormuz event and contextualizes it against historical patterns. It does not *fully* answer why the market priced the oil spike as transient.

A complete answer would require additional data not in scope for this version:

- Forward earnings estimates for CVX and peers during the event window
- Sector positioning data (institutional flows, short interest)
- Fundamental metrics like free cash flow yield, capex-to-operating-cash-flow ratio, buyback pace, and dividend coverage
- Oil futures curve structure (backwardation vs contango) at the time of the event

---

## Conclusion

The CVX-WTI relationship is variable, not broken. Rolling correlations have ranged from 0.2 to 0.7 since 2010 with no sustained directional trend, and divergence between energy equities and crude is a recurring rather than novel pattern. What distinguishes the March 2026 Iran/Hormuz event is the speed and magnitude of the decoupling: WTI surged 35.6% in one week while CVX moved 1.7% — a capture rate of just 4.8%, compared to 84.8% during the comparable first week of the 2022 Russia/Ukraine conflict. The decrease in the CVX-WTI spread during the first week of the Iran war was the largest observable decline in the data going back to 2021.

The broader energy sector's mirroring of this move points to a sector-wide interpretation rather than a standalone CVX story. The most likely explanation — though one this dashboard cannot fully confirm — is that the market priced the oil spike as a temporary geopolitical risk premium rather than a sustained shift in supply fundamentals that would flow through to energy company earnings. 

---

## Repository Contents

- `data_pull.py` — Master data acquisition script
- `CVX_Oil_Correlation.pbix` — Power BI dashboard file
- `screenshots/` — Page screenshots for reference
- `README.md` — This file
