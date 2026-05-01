"""
Comprehensive Portfolio Analysis — Multi-Source
Pulls data from Yahoo Finance, TradingView, and IBKR to analyze the portfolio.
"""
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import yfinance as yf
from tradingview_ta import TA_Handler, Interval

# ---------------------------------------------------------------------------
# Portfolio (from IBKR paper account, matching RBC real portfolio)
# ---------------------------------------------------------------------------
PORTFOLIO = {
    # symbol: (shares, yf_ticker, tv_symbol, tv_exchange, tv_screener, currency, asset_type)
    "RY":   (510,  "RY.TO",   "RY",   "TSX",    "canada",  "CAD", "Stock"),
    "FSZ":  (2300, "FSZ.TO",  "FSZ",  "TSX",    "canada",  "CAD", "Stock"),
    "META": (20,   "META",    "META", "NASDAQ", "america", "USD", "Stock"),
    "MSFT": (750,  "MSFT",    "MSFT", "NASDAQ", "america", "CAD", "CDR"),   # CDR
    "ORCL": (40,   "ORCL",    "ORCL", "NYSE",   "america", "USD", "Stock"),
    "SIRI": (80,   "SIRI",    "SIRI", "NASDAQ", "america", "USD", "Stock"),
    "STZ":  (200,  "STZ",     "STZ",  "NYSE",   "america", "USD", "CDR"),   # CDR
    "KULR": (125,  "KULR",    "KULR", "AMEX",   "america", "USD", "Stock"),
    "QQQ":  (15,   "QQQ",     "QQQ",  "NASDAQ", "america", "USD", "ETF"),
    "VCN":  (200,  "VCN.TO",  "VCN",  "TSX",    "canada",  "CAD", "ETF"),
    "XAW":  (220,  "XAW.TO",  "XAW",  "TSX",    "canada",  "CAD", "ETF"),
    "ZEA":  (500,  "ZEA.TO",  "ZEA",  "TSX",    "canada",  "CAD", "ETF"),
    "XIT":  (140,  "XIT.TO",  "XIT",  "TSX",    "canada",  "CAD", "ETF"),
    "XEC":  (250,  "XEC.TO",  "XEC",  "TSX",    "canada",  "CAD", "ETF"),
    "ZAG":  (1500, "ZAG.TO",  "ZAG",  "TSX",    "canada",  "CAD", "ETF"),
    "ZEM":  (127,  "ZEM.TO",  "ZEM",  "TSX",    "canada",  "CAD", "ETF"),
    "XRP":  (100,  "XRP.TO",  "XRP",  "TSX",    "canada",  "CAD", "ETF"),
}

CASH_CAD = 43409.23
BNS597_VALUE = 18420.35

# Get USD/CAD
fx = yf.Ticker("USDCAD=X")
USDCAD = fx.info.get("regularMarketPrice") or 1.38
print(f"USD/CAD: {USDCAD:.4f}\n")

results = []

for symbol, (shares, yf_ticker, tv_sym, tv_exch, tv_screen, currency, asset_type) in PORTFOLIO.items():
    print(f"Analyzing {symbol}...", flush=True)
    data = {"symbol": symbol, "shares": shares, "currency": currency, "asset_type": asset_type}

    # --- Yahoo Finance ---
    try:
        info = yf.Ticker(yf_ticker).info
        price = info.get("regularMarketPrice") or info.get("previousClose") or 0
        data["price"] = price
        data["yf_recommendation"] = info.get("recommendationKey", "N/A")
        data["yf_target"] = info.get("targetMeanPrice")
        data["fwd_pe"] = info.get("forwardPE")
        data["trail_pe"] = info.get("trailingPE")
        data["peg"] = info.get("pegRatio")
        data["roe"] = info.get("returnOnEquity")
        data["profit_margin"] = info.get("profitMargins")
        data["revenue_growth"] = info.get("revenueGrowth")
        data["earnings_growth"] = info.get("earningsGrowth")
        data["dividend_yield"] = info.get("dividendYield")
        data["beta"] = info.get("beta")
        data["de_ratio"] = info.get("debtToEquity")
        data["fcf"] = info.get("freeCashflow")
        data["market_cap"] = info.get("marketCap")
        data["sector"] = info.get("sector", "ETF" if asset_type == "ETF" else "N/A")
        data["52w_high"] = info.get("fiftyTwoWeekHigh")
        data["52w_low"] = info.get("fiftyTwoWeekLow")

        # Calculate market value in CAD
        if currency == "USD":
            data["mkt_value_cad"] = shares * price * USDCAD
        else:
            data["mkt_value_cad"] = shares * price
    except Exception as e:
        data["price"] = 0
        data["mkt_value_cad"] = 0
        data["yf_error"] = str(e)

    # --- TradingView ---
    try:
        handler = TA_Handler(symbol=tv_sym, screener=tv_screen, exchange=tv_exch, interval=Interval.INTERVAL_1_DAY)
        analysis = handler.get_analysis()
        data["tv_recommendation"] = analysis.summary.get("RECOMMENDATION", "N/A")
        data["tv_buy"] = analysis.summary.get("BUY", 0)
        data["tv_sell"] = analysis.summary.get("SELL", 0)
        data["tv_neutral"] = analysis.summary.get("NEUTRAL", 0)
        data["rsi"] = round(analysis.indicators.get("RSI", 0) or 0, 1)
        data["macd"] = round(analysis.indicators.get("MACD.macd", 0) or 0, 4)
        data["macd_signal"] = round(analysis.indicators.get("MACD.signal", 0) or 0, 4)
        data["adx"] = round(analysis.indicators.get("ADX", 0) or 0, 1)
        data["stoch_k"] = round(analysis.indicators.get("Stoch.K", 0) or 0, 1)
    except Exception as e:
        data["tv_recommendation"] = "ERROR"
        data["rsi"] = 0

    results.append(data)

# Add BNS597 manually
results.append({
    "symbol": "BNS597", "shares": 909, "currency": "CAD", "asset_type": "Mutual Fund",
    "price": 20.27, "mkt_value_cad": BNS597_VALUE,
    "yf_recommendation": "N/A", "tv_recommendation": "N/A", "rsi": 0,
    "sector": "Mutual Fund",
})

# Save to JSON for the analysis artifact
output = {
    "usdcad": USDCAD,
    "cash_cad": CASH_CAD,
    "bns597_value": BNS597_VALUE,
    "holdings": results,
}

with open("scratch_portfolio_analysis.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print("\nData saved to scratch_portfolio_analysis.json")
print(f"Analyzed {len(results)} holdings.")
