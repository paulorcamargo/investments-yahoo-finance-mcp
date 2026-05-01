"""Quick RSI rankings for 60+ quality stocks."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from tradingview_ta import TA_Handler, Interval

STOCKS = {
    'META':('NASDAQ','america'), 'NVDA':('NASDAQ','america'), 'AMZN':('NASDAQ','america'),
    'GOOGL':('NASDAQ','america'), 'AAPL':('NASDAQ','america'), 'MSFT':('NASDAQ','america'),
    'AVGO':('NASDAQ','america'), 'UNH':('NYSE','america'), 'JNJ':('NYSE','america'),
    'PG':('NYSE','america'), 'LLY':('NYSE','america'), 'MRK':('NYSE','america'),
    'PFE':('NYSE','america'), 'NKE':('NYSE','america'), 'DIS':('NYSE','america'),
    'INTC':('NASDAQ','america'), 'BA':('NYSE','america'), 'TGT':('NYSE','america'),
    'PYPL':('NASDAQ','america'), 'STZ':('NYSE','america'), 'ABBV':('NYSE','america'),
    'CVX':('NYSE','america'), 'XOM':('NYSE','america'), 'DE':('NYSE','america'),
    'ABNB':('NASDAQ','america'), 'SHOP':('NYSE','america'), 'BNS':('TSX','canada'),
    'ENB':('TSX','canada'), 'SU':('TSX','canada'), 'VZ':('NYSE','america'),
    'KO':('NYSE','america'), 'PEP':('NASDAQ','america'), 'COST':('NASDAQ','america'),
    'HD':('NYSE','america'), 'LOW':('NYSE','america'), 'MCD':('NYSE','america'),
    'SBUX':('NASDAQ','america'), 'AMD':('NASDAQ','america'), 'CRM':('NYSE','america'),
    'JPM':('NYSE','america'), 'V':('NYSE','america'), 'MA':('NYSE','america'),
    'LMT':('NYSE','america'), 'RTX':('NYSE','america'), 'GD':('NYSE','america'),
    'NOC':('NYSE','america'), 'ORCL':('NYSE','america'), 'BCE':('TSX','canada'),
    'TD':('TSX','canada'), 'BMO':('TSX','canada'), 'CM':('TSX','canada'),
    'CAT':('NYSE','america'), 'IBM':('NYSE','america'), 'NFLX':('NASDAQ','america'),
    'WMT':('NYSE','america'), 'UBER':('NYSE','america'), 'BRK.B':('NYSE','america'),
}

import time

results = []
count = 0
total = len(STOCKS)
for sym, (exch, scr) in STOCKS.items():
    count += 1
    try:
        h = TA_Handler(symbol=sym, screener=scr, exchange=exch, interval=Interval.INTERVAL_1_DAY)
        a = h.get_analysis()
        rsi = a.indicators.get('RSI', 50) or 50
        stk = a.indicators.get('Stoch.K', 50) or 50
        rec = a.summary.get('RECOMMENDATION', 'N/A')
        results.append((sym, round(rsi, 1), round(stk, 1), rec))
        if count % 10 == 0:
            print(f"  Scanned {count}/{total}...", flush=True)
    except Exception as e:
        print(f"  Error {sym}: {e}", flush=True)
    time.sleep(0.3)

results.sort(key=lambda x: x[1])

print("TOP 25 LOWEST RSI (from 56 quality stocks scanned)")
print("=" * 60)
print("  Sym       RSI   Stoch K   TV Signal       Status")
print("-" * 60)
for sym, rsi, stk, rec in results[:25]:
    if rsi <= 30:
        status = "<<< OVERSOLD"
    elif rsi <= 40:
        status = "<< NEAR OVERSOLD"
    elif rsi <= 45:
        status = "< APPROACHING"
    else:
        status = ""
    print(f"  {sym:<8s} {rsi:>5.1f}   {stk:>5.1f}   {rec:<14s}  {status}")

print("-" * 60)
print(f"\n  Lowest RSI found: {results[0][0]} at {results[0][1]}")
print(f"  Stocks with RSI <= 30: {sum(1 for r in results if r[1] <= 30)}")
print(f"  Stocks with RSI <= 40: {sum(1 for r in results if r[1] <= 40)}")
print(f"  Stocks with RSI <= 50: {sum(1 for r in results if r[1] <= 50)}")
