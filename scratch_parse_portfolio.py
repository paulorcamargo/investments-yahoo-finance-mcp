"""Parse RBC portfolio CSV and summarize holdings."""
import csv
import io

with open(r'C:\Users\Paulo\Downloads\Holdings Retirement May 1, 2026.csv', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
data_lines = [l for l in lines[13:33] if l.strip() and ',' in l]

holdings = {}
for line in data_lines:
    reader = csv.reader(io.StringIO(line))
    for row in reader:
        if len(row) < 13:
            continue
        acct_type = row[1].strip().replace('"', '')
        product = row[4].strip().replace('"', '')
        symbol = row[5].strip()
        qty_str = row[6].strip().replace('"', '').replace(',', '')
        price_str = row[7].strip().replace('"', '')
        currency = row[8].strip()
        mkt_value_str = row[12].strip().replace('"', '').replace(',', '')

        try:
            q = float(qty_str)
        except ValueError:
            q = 0

        try:
            mv = float(mkt_value_str)
        except ValueError:
            mv = 0

        if symbol in holdings:
            holdings[symbol]['qty'] += q
            holdings[symbol]['mkt_value'] += mv
            holdings[symbol]['accounts'].append(acct_type)
        else:
            holdings[symbol] = {
                'qty': q,
                'price': price_str,
                'currency': currency,
                'product': product,
                'accounts': [acct_type],
                'mkt_value': mv,
            }

print(f"{'Symbol':8s} {'Qty':>10s} {'Price':>10s} {'Mkt Value':>14s} {'Type':15s} Accounts")
print("=" * 80)
total = 0
for sym, d in sorted(holdings.items()):
    total += d['mkt_value']
    accts = ' + '.join(d['accounts'])
    print(f"{sym:8s} {d['qty']:>10.1f} {d['price']:>10s} ${d['mkt_value']:>13,.2f} {d['product']:15s} {accts}")
print(f"\n{'TOTAL':8s} {'':>10s} {'':>10s} ${total:>13,.2f}")
