# Investment Research Sources — Reference Guide

> **Purpose:** This document maps every recommended financial data source to its
> integration status in this MCP toolkit, the Python library or API used, and
> practical notes on cost, accuracy, and when to use each one.

---

## Quick-Reference Matrix

| # | Source | Category | Integrated? | Library / API | Cost |
|---|--------|----------|:-----------:|---------------|------|
| 1 | **SEC EDGAR** | Regulatory Filings | ✅ `sec_edgar_mcp.py` | `edgartools` | Free |
| 2 | **SEDAR+** | Regulatory Filings (Canada) | ❌ No API | Web only — [sedarplus.ca](https://www.sedarplus.ca/) | Free (manual) |
| 3 | **Investment Company Institute (ICI)** | Fund Industry Stats | ❌ No API | Excel downloads — [ici.org/statistics](https://www.ici.org/research/statistics) | Free (manual) |
| 4 | **Morningstar Investor** | Fundamental Research | ✅ `morningstar_mcp.py` | `mstarpy` + Selenium | Free (unofficial) |
| 5 | **Seeking Alpha** | Crowdsourced Research | ❌ Anti-bot protected | No free programmatic access | Paid sub |
| 6 | **ValueInvesting.io** | DCF / Intrinsic Value | ❌ Paid API | REST API (Global Plan, ~\$30/mo) | Paid |
| 7 | **Bloomberg Terminal** | Institutional News & Data | ❌ Terminal only | Bloomberg API (B-PIPE / DAPI) | ~\$25k/yr |
| 8 | **LSEG Workspace (Eikon)** | Institutional Analytics | ❌ Desktop only | Eikon Data API / Refinitiv | ~\$22k/yr |
| 9 | **Moody's** | Credit Ratings & Risk | ❌ Enterprise only | CreditView API | Enterprise |
| 10 | **TradingView** | Technical Analysis | ✅ `tradingview_mcp.py` | `tradingview-ta` | Free |
| 11 | **Deeptracker AI** | AI Event Signals | ❌ Paid SaaS | Proprietary API | Paid |
| 12 | **Yahoo Finance** | Market Data & Fundamentals | ✅ `yahoo_finance_mcp.py` | `yfinance` | Free |

---

## 1. Primary & Regulatory Sources (The Gold Standard)

### SEC EDGAR Database — ✅ Integrated
- **MCP Server:** `sec_edgar_mcp.py`
- **Library:** [`edgartools`](https://pypi.org/project/edgartools/) (MIT, free, no API key)
- **Tools provided:**
  - `edgar_search_company` — Look up any US public company by ticker or CIK
  - `edgar_get_filings` — Retrieve 10-K, 10-Q, 8-K, 13F, S-1, DEF 14A, Form 4, etc.
  - `edgar_get_financials` — Extract XBRL-parsed income statement, balance sheet, cash flow
  - `edgar_get_insider_transactions` — Form 4 insider buys/sells
  - `edgar_get_company_facts` — XBRL time-series for any reported metric
  - `edgar_full_text_search` — Full-text search across all EDGAR filings (EFTS)
- **Rate limit:** 10 requests/second per SEC policy
- **Accuracy:** ★★★★★ — This *is* the official data companies are legally required to file.

### SEDAR+ (Canada) — ❌ Manual Only
- **Status:** No public API exists. The CSA has stated APIs are a longer-term goal.
- **How to use:** Browse filings at [sedarplus.ca](https://www.sedarplus.ca/)
- **Workaround:** For TSX-listed companies that also file in the US (dual-listed), use
  SEC EDGAR instead (e.g., RY, TD, BMO all file 20-F or 40-F with the SEC).

### Investment Company Institute (ICI) — ❌ Manual Only
- **Status:** No public API. Data published as HTML pages and Excel spreadsheets.
- **How to use:** Download weekly fund flow reports from [ici.org/statistics](https://www.ici.org/research/statistics)
- **Workaround:** Use `pandas.read_excel()` with the direct download URL for automation.
- **Alternative:** Morningstar fund tools (`get_fund_overview`, `get_fund_holdings`,
  `get_fund_performance`) provide similar fund-level data via `morningstar_mcp.py`.

---

## 2. Fundamental Research & Analysis

### Morningstar Investor — ✅ Integrated
- **MCP Server:** `morningstar_mcp.py`
- **Library:** [`mstarpy`](https://pypi.org/project/mstarpy/) (requires one-time Selenium session)
- **Tools provided:**
  - `search_security` — Search stocks and funds
  - `get_stock_overview` / `get_stock_analysis` — Star rating, moat, fair value
  - `get_stock_financials` / `get_stock_valuation` / `get_stock_key_ratios`
  - `get_stock_ownership` / `get_stock_esg` / `get_stock_dividends`
  - `get_fund_overview` / `get_fund_holdings` / `get_fund_performance`
- **Accuracy:** ★★★★★ — Independent analyst ratings; the "moat" framework is unique to Morningstar.

### Seeking Alpha — ❌ Not Integrable (Free)
- **Status:** No free API. Heavy anti-bot protection (Cloudflare + DataDome).
- **Workaround:** Use Morningstar for analyst-grade ratings, and Yahoo Finance for
  consensus recommendations from Wall Street analysts. Both are integrated.
- **If needed:** Paid plans offer limited API access; evaluate [seekingalpha.com/api](https://seekingalpha.com).

### ValueInvesting.io — ❌ Paid API Only
- **Status:** REST API requires a "Global Plan" subscription (~\$30/month).
- **Endpoint:** `https://valueinvesting.io/api/valuation?tickers=AAPL&api_key=YOUR_KEY`
- **Workaround:** Build your own DCF model using data from `yahoo_finance_mcp.py`
  (financial statements) + `numpy-financial` for NPV calculations. See the
  `screener.py` module for a template approach.

---

## 3. Institutional-Grade News & Data

### Bloomberg Terminal — ❌ Not Integrable
- **Cost:** ~\$25,000/year per terminal seat
- **Notes:** Bloomberg provides the B-PIPE and Desktop API (DAPI) for programmatic
  access, but only from an active terminal session. Not suitable for MCP integration
  without an existing Bloomberg subscription.

### LSEG Workspace (formerly Eikon) — ❌ Not Integrable
- **Cost:** ~\$22,000/year
- **Notes:** Offers the Eikon Data API and Refinitiv Python library for professional
  analytics and Reuters news. Requires an active desktop license.

### Moody's — ❌ Enterprise Only
- **Notes:** CreditView platform provides ratings and research. Access is
  institutional-only with enterprise pricing.
- **Workaround:** For basic credit-risk context, check the "debt" and "leverage"
  sections of Morningstar's key ratios (`get_stock_key_ratios`), or review debt
  disclosures in SEC 10-K filings (`edgar_get_financials` → balance sheet).

---

## 4. Technical Analysis & Real-Time Alerts

### TradingView — ✅ Integrated
- **MCP Server:** `tradingview_mcp.py`
- **Library:** [`tradingview-ta`](https://pypi.org/project/tradingview-ta/) (unofficial, free, no API key)
- **Tools provided:**
  - `tv_get_analysis` — Full analysis with all indicators and recommendations
  - `tv_get_summary` — Quick BUY/SELL/NEUTRAL signal counts
  - `tv_multi_timeframe` — 15m → 1W alignment check across 5 timeframes
  - `tv_get_indicators` — Raw values: RSI, MACD, Stochastic, ADX, CCI, ATR,
    Bollinger Bands, SMA/EMA (10/20/50/100/200), Ichimoku, Williams %R, etc.
  - `tv_compare_tickers` — Side-by-side comparison for up to 10 tickers
- **Exchanges supported:** NASDAQ, NYSE, AMEX, TSX, LSE, XETRA, ASX, NSE, HKEX, BINANCE, and more.
- **Accuracy:** ★★★★☆ — Pre-calculated by TradingView's engine; very fast but depends
  on their data feed. Cross-reference with Yahoo Finance historical data for validation.

### Deeptracker AI — ❌ Paid SaaS
- **Status:** Proprietary AI platform for event-driven signals. No free API.
- **Workaround:** Use TradingView for technical signals and SEC EDGAR full-text search
  (`edgar_full_text_search`) to find real-world event disclosures manually.

---

## 5. Already Integrated: Yahoo Finance

### Yahoo Finance — ✅ Integrated
- **MCP Server:** `yahoo_finance_mcp.py`
- **Library:** [`yfinance`](https://pypi.org/project/yfinance/) (free, no API key)
- **Tools provided:**
  - `get_ticker_info` — Company profile, PE ratio, dividend yield, market cap
  - `get_historical_data` — OHLCV price history (1 minute to max history)
  - `get_financial_statements` — Income, balance, cash flow statements
  - `get_news` — Recent news articles
  - `get_options_chain` — Options expirations, calls, puts
  - `get_analyst_recommendations` — Wall Street consensus ratings & price targets
  - `get_institutional_holders` — Top institutional owners

---

## Pro Tips for Maximum Accuracy

> **Accuracy lies in the consensus.** Most professional investors compare estimates from
> multiple sources rather than trusting a single analyst.

### Cross-Reference Strategy
1. **Start with SEC EDGAR** for the "ground truth" — these are legally audited numbers.
2. **Check Morningstar** for independent valuation (star rating, moat, fair value).
3. **Validate with Yahoo Finance** for Wall Street consensus targets and real-time prices.
4. **Confirm with TradingView** for technical timing signals (is it a good *entry point*?).

### Recommended Workflow
```
SEC EDGAR (truth) → Morningstar (quality) → Yahoo Finance (consensus) → TradingView (timing)
```

### For Canadian Securities
- **Dual-listed companies** (RY, TD, BMO, etc.): Use SEC EDGAR for filings + Yahoo Finance
  with `.TO` suffix for TSX pricing.
- **TSX-only companies**: Use Morningstar (supports Canadian stocks) + TradingView
  (exchange="TSX") for technical analysis.
- **SEDAR+**: Check manually at [sedarplus.ca](https://www.sedarplus.ca/) for regulatory filings
  not available through SEC EDGAR.

---

## MCP Server Configuration

To use all four MCP servers, add these entries to your `mcp_config.json`:

```json
{
  "servers": {
    "yahoo-finance": {
      "command": "python",
      "args": ["yahoo_finance_mcp.py"],
      "transport": "stdio"
    },
    "morningstar": {
      "command": "python",
      "args": ["morningstar_mcp.py"],
      "transport": "stdio"
    },
    "sec-edgar": {
      "command": "python",
      "args": ["sec_edgar_mcp.py"],
      "transport": "stdio"
    },
    "tradingview": {
      "command": "python",
      "args": ["tradingview_mcp.py"],
      "transport": "stdio"
    }
  }
}
```

> [!IMPORTANT]
> For SEC EDGAR, update the identity string in `sec_edgar_mcp.py` line 27 with your
> actual name and email. The SEC requires this for all API access.

---

*Last updated: April 30, 2026*
