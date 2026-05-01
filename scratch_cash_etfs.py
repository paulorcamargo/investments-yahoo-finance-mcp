"""Quick comparison of cash-parking ETFs."""
import yfinance as yf

tickers = {
    # Canadian HISA ETFs (CAD)
    "CASH.TO": "Global X HISA ETF",
    "PSA.TO": "Purpose HISA ETF",
    "CSAV.TO": "CI HISA ETF",
    "HSAV.TO": "Global X HISA (Tax-Eff)",
    # US Treasury / Money Market ETFs (USD)
    "SGOV": "iShares 0-3M Treasury",
    "BIL": "SPDR 1-3M T-Bill",
    "SHV": "iShares Short Treasury",
    "USFR": "WisdomTree Float Rate",
}

print(f"{'Ticker':10s} {'Name':30s} {'Price':>8s} {'Yield%':>8s} {'MER%':>8s}")
print("=" * 70)

for ticker, name in tickers.items():
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice") or info.get("previousClose") or 0
        yld = (info.get("yield") or 0) * 100
        mer = (info.get("annualReportExpenseRatio") or 0) * 100
        print(f"{ticker:10s} {name:30s} {price:>8.2f} {yld:>7.2f}% {mer:>7.2f}%")
    except Exception as e:
        print(f"{ticker:10s} {name:30s} {'ERROR':>8s}  {str(e)[:30]}")
