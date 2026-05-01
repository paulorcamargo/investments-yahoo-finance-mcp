"""Corrected portfolio analysis using actual RBC CSV prices for CDRs."""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load TradingView/YF signal data from previous analysis
with open('scratch_portfolio_analysis.json', 'r') as f:
    raw = json.load(f)

# Build signal lookup
signals = {}
for h in raw['holdings']:
    signals[h['symbol']] = h

# CORRECT portfolio values from RBC CSV (all in CAD)
PORTFOLIO = [
    # (symbol, shares, price_cad, mkt_value_cad, asset_type, sector_or_geo)
    ("RY",     510,   243.67,  124271.70, "Stock",       "Canada"),
    ("META",   620,    58.50,   36270.88, "Stock/CDR",   "US"),       # blended: 20 full + 600 CDR
    ("MSFT",   750,    29.18,   21885.00, "CDR",         "US"),       # CDR on TSE
    ("ZAG",   1500,    13.70,   20550.00, "Bond ETF",    "Canada-Bond"),
    ("BNS597", 909,    20.27,   18420.35, "Mutual Fund", "Canada"),
    ("ZEA",    500,    29.51,   14755.00, "ETF",         "International"),
    ("VCN",    200,    68.95,   13790.00, "ETF",         "Canada"),
    ("QQQ",     15,   916.08,   13741.26, "ETF",         "US"),
    ("FSZ",   2300,     5.72,   13144.50, "Stock",       "Canada"),
    ("XAW",    220,    54.62,   12016.40, "ETF",         "International"),
    ("XEC",    250,    41.70,   10425.00, "ETF",         "Emerging"),
    ("XIT",    140,    71.27,    9977.80, "ETF",         "Canada"),
    ("ORCL",    40,   235.70,    9427.92, "Stock",       "US"),
    ("ZEM",    127,    31.13,    3953.51, "ETF",         "Emerging"),
    ("SIRI",    80,    37.11,    2969.03, "Stock",       "US"),
    ("STZ",    200,    12.49,    2498.00, "CDR",         "US"),       # CDR on TSE
    ("XRP",    100,     6.10,     610.00, "ETF",         "Crypto"),
    ("KULR",   125,     3.58,     447.44, "Stock",       "US"),
]

CASH = 43409.23
total_invested = sum(p[3] for p in PORTFOLIO)
grand_total = total_invested + CASH

print("=" * 110)
print("  CORRECTED PORTFOLIO ANALYSIS (CDR prices used for MSFT & STZ)")
print(f"  Total: ${grand_total:,.0f} CAD | Invested: ${total_invested:,.0f} | Cash: ${CASH:,.0f}")
print("=" * 110)

header = f"{'Sym':<7s} {'Shrs':>6s} {'Prc CAD':>8s} {'Value':>10s} {'%':>5s} {'YF':>10s} {'TV':>14s} {'RSI':>4s} {'StK':>4s} {'Type':<12s} {'Geo'}"
print(header)
print("-" * 110)

for sym, shares, price, val, atype, geo in sorted(PORTFOLIO, key=lambda x: x[3], reverse=True):
    pct = val / grand_total * 100
    s = signals.get(sym, {})
    yf_rec = s.get('yf_recommendation', 'N/A')
    tv_rec = s.get('tv_recommendation', 'N/A')
    rsi = s.get('rsi', 0)
    stoch = s.get('stoch_k', 0)
    print(f"{sym:<7s} {shares:>6.0f} ${price:>7.2f} ${val:>9,.0f} {pct:>4.1f}% {yf_rec:>10s} {tv_rec:>14s} {rsi:>4.0f} {stoch:>4.0f} {atype:<12s} {geo}")

print(f"{'Cash':<7s} {'':>6s} {'':>8s} ${CASH:>9,.0f} {CASH/grand_total*100:>4.1f}%")
print("-" * 110)
print(f"{'TOTAL':<7s} {'':>6s} {'':>8s} ${grand_total:>9,.0f}")

# Geography
print("\n\nGEOGRAPHY")
print("=" * 55)
geo_map = {}
for sym, shares, price, val, atype, geo in PORTFOLIO:
    base_geo = geo.split('-')[0]  # "Canada-Bond" -> "Canada"
    geo_map[base_geo] = geo_map.get(base_geo, 0) + val

for g, v in sorted(geo_map.items(), key=lambda x: x[1], reverse=True):
    pct = v / grand_total * 100
    bar = '#' * int(pct)
    print(f"  {g:15s}: ${v:>10,.0f} ({pct:>5.1f}%) {bar}")
print(f"  {'Cash':15s}: ${CASH:>10,.0f} ({CASH/grand_total*100:>5.1f}%)")

# Asset type
print("\n\nASSET TYPE")
print("=" * 55)
type_map = {}
for sym, shares, price, val, atype, geo in PORTFOLIO:
    type_map[atype] = type_map.get(atype, 0) + val
for t, v in sorted(type_map.items(), key=lambda x: x[1], reverse=True):
    pct = v / grand_total * 100
    print(f"  {t:15s}: ${v:>10,.0f} ({pct:>5.1f}%)")
print(f"  {'Cash':15s}: ${CASH:>10,.0f} ({CASH/grand_total*100:>5.1f}%)")

# Concentration risk
print("\n\nCONCENTRATION RISK (max 10% per holding recommended)")
print("=" * 55)
for sym, shares, price, val, atype, geo in sorted(PORTFOLIO, key=lambda x: x[3], reverse=True):
    pct = val / grand_total * 100
    if pct > 5:
        flag = " *** OVER 10%" if pct > 10 else ""
        print(f"  {sym:8s}: {pct:>5.1f}% (${val:>10,.0f}){flag}")
