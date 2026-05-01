"""Portfolio RSI(14) Dashboard."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import yfinance as yf
import pandas as pd

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

PORTFOLIO = [
    ('RY', 'RY.TO', 'Stock', 124272),
    ('META', 'META', 'Stock/CDR', 36271),
    ('MSFT', 'MSFT', 'CDR', 21885),
    ('ZAG', 'ZAG.TO', 'Bond ETF', 20550),
    ('BNS597', None, 'Mutual Fund', 18420),
    ('ZEA', 'ZEA.TO', 'ETF', 14755),
    ('VCN', 'VCN.TO', 'ETF', 13790),
    ('QQQ', 'QQQ', 'ETF', 13741),
    ('FSZ', 'FSZ.TO', 'Stock', 13145),
    ('XAW', 'XAW.TO', 'ETF', 12016),
    ('XEC', 'XEC.TO', 'ETF', 10425),
    ('XIT', 'XIT.TO', 'ETF', 9978),
    ('ORCL', 'ORCL', 'Stock', 9428),
    ('ZEM', 'ZEM.TO', 'ETF', 3954),
    ('SIRI', 'SIRI', 'Stock', 2969),
    ('STZ', 'STZ', 'CDR', 2498),
    ('XRP', 'XRP-USD', 'Crypto', 610),
    ('KULR', 'KULR', 'Stock', 447),
]

print('=' * 78)
print('  YOUR PORTFOLIO — RSI(14) Dashboard | May 1, 2026')
print('=' * 78)
print(f"  {'Symbol':<8s} {'Type':<12s} {'Value CAD':>10s} {'Price':>9s} {'RSI(14)':>8s}  Status")
print('-' * 78)

for sym, yf_tk, atype, val in PORTFOLIO:
    if yf_tk is None:
        print(f"  {sym:<8s} {atype:<12s} ${val:>9,d}       N/A      N/A  Mutual Fund")
        continue
    try:
        stock = yf.Ticker(yf_tk)
        hist = stock.history(period='1mo')
        price = hist['Close'].iloc[-1] if len(hist) > 0 else 0
        rsi = calc_rsi(hist['Close'], 14) if len(hist) >= 15 else None
        if rsi is None or pd.isna(rsi):
            print(f"  {sym:<8s} {atype:<12s} ${val:>9,d} ${price:>8.2f}      N/A")
        else:
            rsi_v = round(rsi, 1)
            if rsi_v <= 30:   status = '<<< OVERSOLD'
            elif rsi_v <= 40: status = '<< NEAR OVERSOLD'
            elif rsi_v <= 45: status = '< APPROACHING'
            elif rsi_v >= 70: status = '>>> OVERBOUGHT'
            elif rsi_v >= 60: status = '>> WARM'
            else:             status = '  NEUTRAL'
            print(f"  {sym:<8s} {atype:<12s} ${val:>9,d} ${price:>8.2f}   {rsi_v:>5.1f}  {status}")
    except Exception as e:
        print(f"  {sym:<8s} {atype:<12s} ${val:>9,d}       ERR      ERR  {str(e)[:25]}")

print('-' * 78)
print(f"\n  Legend: <<<OVERSOLD (<=30) | <<NEAR (<=40) | NEUTRAL (40-60) | >>WARM (60-70) | >>>OVERBOUGHT (>=70)")
