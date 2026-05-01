"""Calculate total portfolio value in CAD using RBC CSV prices (all already in CAD)."""

# All values directly from the RBC CSV (May 1, 2026) — already in CAD
HOLDINGS = [
    # (Account, Symbol, Qty, Price CAD, Market Value CAD, Type)
    ("RRSP",  "META",   20,     831.34,   16626.88, "Common Shares"),
    ("TFSA",  "META",   600,     32.74,   19644.00, "CDR"),           # CDR
    ("RRSP",  "RY",     220,    243.67,   53607.40, "Common Shares"),
    ("LIRA",  "RY",     290,    243.67,   70664.30, "Common Shares"),
    ("TFSA",  "SIRI",   80,      37.11,    2969.03, "Common Shares"),
    ("TFSA",  "MSFT",   750,     29.18,   21885.00, "CDR"),           # CDR on TSE
    ("RRSP",  "ORCL",   40,     235.70,    9427.92, "Common Shares"),
    ("RRSP",  "STZ",    200,     12.49,    2498.00, "CDR"),           # CDR
    ("RRSP",  "FSZ",    2300,     5.72,   13144.50, "Common Shares"),
    ("RRSP",  "KULR",   125,      3.58,     447.44, "Common Shares"),
    ("RRSP",  "BNS597", 909,     20.27,   18420.35, "Mutual Fund"),
    ("RRSP",  "VCN",    200,     68.95,   13790.00, "ETF"),
    ("RRSP",  "XAW",    220,     54.62,   12016.40, "ETF"),
    ("TFSA",  "QQQ",    15,     916.08,   13741.26, "ETF"),
    ("RRSP",  "ZEA",    500,     29.51,   14755.00, "ETF"),
    ("TFSA",  "XEC",    250,     41.70,   10425.00, "ETF"),
    ("RRSP",  "ZAG",    1500,    13.70,   20550.00, "ETF"),
    ("TFSA",  "XIT",    140,     71.27,    9977.80, "ETF"),
    ("RRSP",  "XRP",    100,      6.10,     610.00, "ETF"),
    ("LIRA",  "ZEM",    127,     31.13,    3953.51, "ETF"),
]

CASH_CAD = 43409.23

# Aggregate by symbol
aggregated = {}
for acct, sym, qty, price, mv, typ in HOLDINGS:
    if sym in aggregated:
        aggregated[sym]["qty"] += qty
        aggregated[sym]["mkt_value"] += mv
        aggregated[sym]["accounts"].append(acct)
    else:
        aggregated[sym] = {
            "qty": qty,
            "price": price,
            "mkt_value": mv,
            "type": typ,
            "accounts": [acct],
        }

# Print
print("=" * 75)
print("  PORTFOLIO SUMMARY — All Values in CAD (as of May 1, 2026)")
print("=" * 75)
print(f"{'Symbol':8s} {'Qty':>8s} {'Price':>10s} {'Value CAD':>14s} {'% Port':>7s} {'Type':15s} Accounts")
print("-" * 75)

total_investments = 0
rows = []
for sym, d in aggregated.items():
    total_investments += d["mkt_value"]
    rows.append((sym, d))

# Sort by market value descending
rows.sort(key=lambda x: x[1]["mkt_value"], reverse=True)

grand_total = total_investments + CASH_CAD

for sym, d in rows:
    pct = (d["mkt_value"] / grand_total) * 100
    accts = "+".join(d["accounts"])
    print(f"{sym:8s} {d['qty']:>8.0f} ${d['price']:>8.2f} ${d['mkt_value']:>13,.2f} {pct:>6.1f}% {d['type']:15s} {accts}")

print("-" * 75)
print(f"\n{'INVESTMENTS:':>20s} ${total_investments:>13,.2f} CAD")
print(f"{'CASH:':>20s} ${CASH_CAD:>13,.2f} CAD")
print(f"{'':>20s}  {'_'*14}")
print(f"{'TOTAL PORTFOLIO:':>20s} ${grand_total:>13,.2f} CAD")

# By account type
print(f"\n{'BY ACCOUNT':>20s}")
print("-" * 40)
by_acct = {}
for acct, sym, qty, price, mv, typ in HOLDINGS:
    by_acct[acct] = by_acct.get(acct, 0) + mv

for acct, val in sorted(by_acct.items()):
    print(f"{acct:>20s}: ${val:>13,.2f} CAD")
print(f"{'Cash':>20s}: ${CASH_CAD:>13,.2f} CAD")
print(f"{'TOTAL':>20s}: ${sum(by_acct.values()) + CASH_CAD:>13,.2f} CAD")

# By asset type
print(f"\n{'BY ASSET TYPE':>20s}")
print("-" * 40)
by_type = {}
for acct, sym, qty, price, mv, typ in HOLDINGS:
    by_type[typ] = by_type.get(typ, 0) + mv
for typ, val in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    pct = (val / grand_total) * 100
    print(f"{typ:>20s}: ${val:>13,.2f} CAD  ({pct:.1f}%)")
print(f"{'Cash':>20s}: ${CASH_CAD:>13,.2f} CAD  ({CASH_CAD/grand_total*100:.1f}%)")
