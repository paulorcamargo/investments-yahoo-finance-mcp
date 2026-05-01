"""
Oversold Quality Screener using Yahoo Finance only (no TradingView rate limits).
Calculates RSI(14) from price history + gets analyst recommendations.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import yfinance as yf
import pandas as pd
import numpy as np

def calc_rsi(prices, period=14):
    """Calculate RSI from price series."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# 60+ quality tickers to scan
TICKERS = [
    # US Mega Cap
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "AVGO", "BRK-B",
    "JPM", "V", "MA", "UNH", "JNJ", "PG", "COST", "HD", "LLY", "ABBV",
    "MRK", "PFE", "KO", "PEP", "WMT", "DIS", "NFLX", "CRM", "AMD",
    "INTC", "CSCO", "BA", "CAT", "DE", "GE", "NKE", "SBUX", "MCD",
    "TGT", "LOW", "CVX", "XOM", "PYPL", "SHOP", "UBER", "ABNB",
    # Defense
    "LMT", "RTX", "GD", "NOC",
    # Dividends
    "T", "VZ", "IBM", "O",
    # Additional quality
    "ORCL", "STZ", "ADBE", "NOW", "ISRG", "PANW", "SNOW",
    # Canadian (use .TO)
    "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "ENB.TO", "SU.TO", "CNQ.TO", "BCE.TO",
    # ETFs
    "QQQ", "SPY", "IWM", "EFA", "EEM", "ITA", "SMH", "XLK", "XLV", "XLE",
]

results = []
count = 0
total = len(TICKERS)

for ticker in TICKERS:
    count += 1
    if count % 10 == 0:
        print(f"  Scanning {count}/{total}...", flush=True)
    try:
        stock = yf.Ticker(ticker)

        # Get 1 month of daily prices for RSI calc
        hist = stock.history(period="1mo")
        if len(hist) < 15:
            continue
        rsi = calc_rsi(hist['Close'], 14)
        if pd.isna(rsi):
            continue

        info = stock.info
        price = info.get("regularMarketPrice") or info.get("previousClose") or 0
        yf_rec = info.get("recommendationKey", "N/A")
        fwd_pe = info.get("forwardPE")
        roe = info.get("returnOnEquity")
        rev_growth = info.get("revenueGrowth")
        profit_margin = info.get("profitMargins")
        div_yield = info.get("dividendYield")
        beta = info.get("beta")
        target = info.get("targetMeanPrice")
        high52 = info.get("fiftyTwoWeekHigh", 0)
        low52 = info.get("fiftyTwoWeekLow", 0)
        sector = info.get("sector", "ETF")
        market_cap = info.get("marketCap", 0)
        name = info.get("shortName", ticker)

        upside = ((target / price) - 1) * 100 if target and price and price > 0 else 0
        off_high = ((price / high52) - 1) * 100 if high52 and high52 > 0 else 0

        results.append({
            "ticker": ticker,
            "name": name[:25],
            "price": price,
            "rsi": round(rsi, 1),
            "yf_rec": yf_rec,
            "fwd_pe": fwd_pe,
            "roe": roe,
            "rev_growth": rev_growth,
            "div_yield": div_yield,
            "beta": beta,
            "upside": round(upside, 1),
            "off_high": round(off_high, 1),
            "sector": sector,
        })
    except Exception as e:
        pass

# Sort by RSI
results.sort(key=lambda x: x["rsi"])

# Print results
print(f"\n{'='*115}")
print(f"  OVERSOLD QUALITY SCREENER — RSI(14) Rankings ({len(results)} stocks scanned)")
print(f"  Sorted by RSI ascending | May 1, 2026")
print(f"{'='*115}")

header = f"  {'Ticker':<8s} {'Name':<26s} {'Price':>8s} {'RSI':>5s} {'YF Rec':>11s} {'FwdPE':>6s} {'Upside':>7s} {'Off Hi':>7s} {'Div%':>5s} {'Sector':>15s}"
print(header)
print("-" * 115)

oversold_count = 0
for r in results[:30]:  # Show top 30 lowest RSI
    fpe = f"{r['fwd_pe']:.1f}" if r['fwd_pe'] else "  N/A"
    dy = f"{r['div_yield']*100:.1f}%" if r['div_yield'] else " N/A"
    sect = (r['sector'] or 'N/A')[:15]

    # Flag oversold
    if r['rsi'] <= 30:
        flag = " <<< OVERSOLD"
        oversold_count += 1
    elif r['rsi'] <= 40:
        flag = " << NEAR"
    elif r['rsi'] <= 45:
        flag = " <"
    else:
        flag = ""

    # Highlight strong buys
    star = " ***" if r['yf_rec'] in ('buy', 'strong_buy') and r['rsi'] <= 45 else ""

    print(f"  {r['ticker']:<8s} {r['name']:<26s} ${r['price']:>7.2f} {r['rsi']:>5.1f} {r['yf_rec']:>11s} {fpe:>6s} {r['upside']:>6.1f}% {r['off_high']:>6.1f}% {dy:>5s} {sect:>15s}{flag}{star}")

print("-" * 115)
print(f"\n  Summary:")
print(f"  - RSI <= 30 (Oversold):      {oversold_count}")
print(f"  - RSI <= 40 (Near Oversold): {sum(1 for r in results if r['rsi'] <= 40)}")
print(f"  - RSI <= 45 (Approaching):   {sum(1 for r in results if r['rsi'] <= 45)}")
print(f"  - *** = Buy-rated AND RSI <= 45 (best opportunities)")
