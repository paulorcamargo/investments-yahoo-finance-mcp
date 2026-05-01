"""Print portfolio analysis from JSON data."""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('scratch_portfolio_analysis.json', 'r') as f:
    data = json.load(f)

total_invested = sum(h.get('mkt_value_cad', 0) for h in data['holdings'])
grand_total = total_invested + data['cash_cad']

# Print each holding
print("=" * 120)
print("  PORTFOLIO ANALYSIS — Yahoo Finance + TradingView (May 1, 2026)")
print("=" * 120)

header = (
    f"{'Sym':<7s} {'Shrs':>6s} {'Price':>9s} {'Val CAD':>10s} {'%':>5s} "
    f"{'YF':>10s} {'TV':>14s} {'RSI':>4s} {'FwdPE':>6s} {'Div%':>5s} "
    f"{'RevG':>6s} {'Beta':>5s} {'ROE':>6s}"
)
print(header)
print("-" * 120)

for h in sorted(data['holdings'], key=lambda x: x.get('mkt_value_cad', 0), reverse=True):
    sym = h['symbol']
    shares = h.get('shares', 0)
    price = h.get('price', 0)
    val = h.get('mkt_value_cad', 0)
    pct = (val / grand_total * 100) if grand_total > 0 else 0

    yf_rec = h.get('yf_recommendation', 'N/A')
    tv_rec = h.get('tv_recommendation', 'N/A')
    rsi = h.get('rsi', 0)
    fwd_pe = h.get('fwd_pe')
    div_y = h.get('dividend_yield')
    rev_g = h.get('revenue_growth')
    beta = h.get('beta')
    roe = h.get('roe')

    fwd_pe_s = f"{fwd_pe:.1f}" if fwd_pe else "  N/A"
    div_s = f"{div_y*100:.1f}%" if div_y else " N/A"
    rev_s = f"{rev_g*100:.1f}%" if rev_g else "  N/A"
    beta_s = f"{beta:.2f}" if beta else " N/A"
    roe_s = f"{roe*100:.1f}%" if roe else "  N/A"

    line = (
        f"{sym:<7s} {shares:>6.0f} ${price:>8.2f} ${val:>9,.0f} {pct:>4.1f}% "
        f"{yf_rec:>10s} {tv_rec:>14s} {rsi:>4.0f} {fwd_pe_s:>6s} {div_s:>5s} "
        f"{rev_s:>6s} {beta_s:>5s} {roe_s:>6s}"
    )
    print(line)

print("-" * 120)
print(f"Investments: ${total_invested:,.0f} CAD | Cash: ${data['cash_cad']:,.0f} CAD | TOTAL: ${grand_total:,.0f} CAD")

# Geography breakdown
print("\n\nGEOGRAPHY BREAKDOWN")
print("=" * 55)
geo = {'Canada': 0, 'US': 0, 'International': 0, 'Emerging': 0, 'Bonds': 0, 'Crypto': 0, 'Other': 0}
for h in data['holdings']:
    val = h.get('mkt_value_cad', 0)
    sym = h['symbol']
    if sym in ['RY', 'FSZ', 'VCN', 'XIT', 'MSFT']:
        geo['Canada'] += val
    elif sym in ['META', 'ORCL', 'SIRI', 'STZ', 'KULR', 'QQQ']:
        geo['US'] += val
    elif sym in ['XAW', 'ZEA']:
        geo['International'] += val
    elif sym in ['XEC', 'ZEM']:
        geo['Emerging'] += val
    elif sym == 'ZAG':
        geo['Bond'] = geo.get('Bonds', 0) + val
    elif sym == 'XRP':
        geo['Crypto'] += val
    elif sym == 'BNS597':
        geo['Other'] += val

for g, v in sorted(geo.items(), key=lambda x: x[1], reverse=True):
    if v > 0:
        pct = v / grand_total * 100
        bar = "#" * int(pct)
        print(f"  {g:15s}: ${v:>10,.0f} ({pct:>5.1f}%) {bar}")

cash_pct = data['cash_cad'] / grand_total * 100
print(f"  {'Cash':15s}: ${data['cash_cad']:>10,.0f} ({cash_pct:>5.1f}%)")
print(f"  {'TOTAL':15s}: ${grand_total:>10,.0f}")

# Asset type breakdown
print("\n\nASSET TYPE BREAKDOWN")
print("=" * 55)
by_type = {}
for h in data['holdings']:
    t = h.get('asset_type', 'Other')
    by_type[t] = by_type.get(t, 0) + h.get('mkt_value_cad', 0)

for t, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    pct = v / grand_total * 100
    print(f"  {t:15s}: ${v:>10,.0f} ({pct:>5.1f}%)")
print(f"  {'Cash':15s}: ${data['cash_cad']:>10,.0f} ({cash_pct:>5.1f}%)")
