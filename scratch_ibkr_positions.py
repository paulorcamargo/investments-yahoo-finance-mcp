"""Get current IBKR paper account positions."""
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from ib_insync import IB

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=30)

# Get positions
positions = ib.positions()

# Get portfolio with P&L
ib.sleep(2)
portfolio = ib.portfolio()

if not positions:
    print('No open positions.')
else:
    header = f"{'Symbol':8s} {'Shares':>8s} {'Avg Cost':>10s} {'Mkt Price':>10s} {'Mkt Value':>12s} {'Unrl P&L':>12s} {'Curr':>5s}"
    print(header)
    print("=" * len(header))
    
    total_value = 0
    total_pnl = 0
    
    # Build a lookup from portfolio items
    pnl_map = {}
    for item in portfolio:
        pnl_map[item.contract.symbol] = item
    
    for pos in sorted(positions, key=lambda p: p.contract.symbol):
        sym = pos.contract.symbol
        item = pnl_map.get(sym)
        mkt_price = item.marketPrice if item else 0
        mkt_value = item.marketValue if item else 0
        unrealized = item.unrealizedPNL if item else 0
        
        total_value += mkt_value
        total_pnl += unrealized
        
        print(f"{sym:8s} {pos.position:>8.0f} ${pos.avgCost:>9.2f} ${mkt_price:>9.2f} ${mkt_value:>11,.2f} ${unrealized:>11,.2f} {pos.contract.currency:>5s}")
    
    print("=" * len(header))
    print(f"{'TOTAL':8s} {'':>8s} {'':>10s} {'':>10s} ${total_value:>11,.2f} ${total_pnl:>11,.2f}")

ib.disconnect()
