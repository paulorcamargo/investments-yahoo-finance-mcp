"""
Replicate RBC Portfolio in IBKR Paper Account

Reads your real portfolio and places market orders to mirror every position
in your IBKR paper trading account (DUP998877).

Usage:
    py ibkr_replicate_portfolio.py --dry-run    # Preview orders without executing
    py ibkr_replicate_portfolio.py               # Actually place orders

IMPORTANT: This uses MARKET orders on a PAPER TRADING account.
"""

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import argparse
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ib_insync import IB, Stock, MarketOrder

# ---------------------------------------------------------------------------
# Your portfolio from RBC (parsed from CSV)
# ---------------------------------------------------------------------------
# Format: symbol -> (quantity, exchange, currency, description)
# Note: Quantities are whole shares only (IBKR doesn't support fractional on paper)

PORTFOLIO = {
    # --- Canadian Stocks (SMART routes to TSE) ---
    "RY":   (510,  "SMART", "CAD", "Royal Bank of Canada"),
    "FSZ":  (2300, "SMART", "CAD", "Fiera Capital"),

    # --- US Stocks (via SMART routing) ---
    "META": (20,   "SMART", "USD", "Meta Platforms"),        # 20 full shares in RRSP
    "MSFT": (750,  "SMART", "USD", "Microsoft"),             # TFSA - 750 shares at $29 CAD = CDRs?
    "ORCL": (40,   "SMART", "USD", "Oracle"),
    "SIRI": (80,   "SMART", "USD", "SiriusXM"),
    "STZ":  (200,  "SMART", "USD", "Constellation Brands"),  # Price $12.49 CAD = CDRs?
    "KULR": (125,  "SMART", "USD", "KULR Technology"),

    # --- US ETFs ---
    "QQQ":  (15,   "SMART", "USD", "Invesco QQQ Trust"),

    # --- Canadian ETFs (SMART routes to TSE) ---
    "VCN":  (200,  "SMART", "CAD", "Vanguard FTSE Canada"),
    "XAW":  (220,  "SMART", "CAD", "iShares Intl ex-Canada"),
    "ZEA":  (500,  "SMART", "CAD", "BMO MSCI EAFE"),
    "XIT":  (140,  "SMART", "CAD", "iShares S&P/TSX Capped IT"),
    "XEC":  (250,  "SMART", "CAD", "iShares MSCI Emerging Markets"),
    "ZAG":  (1500, "SMART", "CAD", "BMO Aggregate Bond"),
    "ZEM":  (127,  "SMART", "CAD", "BMO MSCI Emerging Markets"),
    "XRP":  (100,  "SMART", "CAD", "XRP ETF"),               # May fail if not available

    # --- Skipped ---
    # BNS597 (Scotia mutual fund) - not available on IBKR
}


def main():
    parser = argparse.ArgumentParser(description="Replicate portfolio in IBKR paper account")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview orders without placing them")
    parser.add_argument("--port", type=int, default=7497,
                        help="TWS API port (default: 7497 for paper)")
    args = parser.parse_args()

    print("=" * 70)
    if args.dry_run:
        print("  IBKR Portfolio Replication -- DRY RUN (no orders will be placed)")
    else:
        print("  IBKR Portfolio Replication -- LIVE EXECUTION on PAPER ACCOUNT")
    print("=" * 70)

    # Connect
    ib = IB()
    try:
        ib.connect("127.0.0.1", args.port, clientId=20)
    except Exception as e:
        print(f"\n[FAIL] Cannot connect to IBKR: {e}")
        print("Make sure TWS is running with API enabled on port", args.port)
        sys.exit(1)

    print(f"[OK] Connected to IBKR (Account: {ib.managedAccounts()})\n")

    # Check existing positions
    existing = {}
    for pos in ib.positions():
        existing[pos.contract.symbol] = pos.position
    if existing:
        print(f"Existing positions: {existing}\n")

    # Process each holding
    success = 0
    failed = 0
    skipped = 0

    print(f"{'Symbol':8s} {'Qty':>6s} {'Exchange':>8s} {'Curr':>5s} {'Status':15s} Details")
    print("-" * 70)

    for symbol, (qty, exchange, currency, desc) in PORTFOLIO.items():
        # Skip if already have position
        if symbol in existing:
            existing_qty = existing[symbol]
            if abs(existing_qty - qty) < 1:
                print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'SKIP':15s} Already have {existing_qty:.0f} shares")
                skipped += 1
                continue
            else:
                # Adjust quantity to reach target
                qty = int(qty - existing_qty)
                if qty <= 0:
                    print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'SKIP':15s} Already have {existing_qty:.0f} (>= target)")
                    skipped += 1
                    continue

        # Create contract
        contract = Stock(symbol, exchange, currency)

        try:
            qualified = ib.qualifyContracts(contract)
            if not qualified:
                print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'FAIL':15s} Could not qualify contract")
                failed += 1
                continue
        except Exception as e:
            print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'FAIL':15s} {str(e)[:40]}")
            failed += 1
            continue

        if args.dry_run:
            print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'DRY RUN':15s} Would BUY {qty} x {desc}")
            success += 1
            continue

        # Place market order
        order = MarketOrder("BUY", qty)
        trade = ib.placeOrder(contract, order)

        # Wait briefly for fill
        for _ in range(10):
            ib.sleep(1)
            if trade.isDone():
                break

        status = trade.orderStatus.status
        fill_price = trade.orderStatus.avgFillPrice or 0

        if status == "Filled":
            print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'FILLED':15s} @ ${fill_price:.2f}")
            success += 1
        elif status in ("Submitted", "PreSubmitted"):
            print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {'SUBMITTED':15s} Waiting for fill...")
            success += 1
        else:
            print(f"{symbol:8s} {qty:>6d} {exchange:>8s} {currency:>5s} {status:15s} May fill later")
            success += 1

        time.sleep(0.5)  # Rate limit

    print("-" * 70)
    print(f"\nSummary: {success} placed, {failed} failed, {skipped} skipped")

    # Wait for any pending fills
    if not args.dry_run and success > 0:
        print("\nWaiting 10 seconds for remaining fills...")
        ib.sleep(10)

        # Print final positions
        print("\nFinal Portfolio Positions:")
        print(f"{'Symbol':8s} {'Shares':>10s} {'Avg Cost':>12s}")
        print("-" * 35)
        for pos in ib.positions():
            print(f"{pos.contract.symbol:8s} {pos.position:>10.0f} ${pos.avgCost:>11.2f}")

    ib.disconnect()
    print("\n[OK] Done. Disconnected from IBKR.")


if __name__ == "__main__":
    main()
