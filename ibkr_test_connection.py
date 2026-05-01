"""
Quick IBKR Connection Test
Tests connectivity to TWS or IB Gateway and retrieves basic account info.

Usage:
    py ibkr_test_connection.py              # Test paper trading (port 7497)
    py ibkr_test_connection.py --live       # Test live trading (port 7496)
"""

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import argparse
import sys
import os

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ib_insync import IB


def test_connection(host="127.0.0.1", port=7497, client_id=99):
    """Attempt to connect to IBKR and print basic account info."""
    ib = IB()

    print(f"[*] Connecting to IBKR at {host}:{port} (clientId={client_id})...")

    try:
        ib.connect(host, port, clientId=client_id)
    except ConnectionRefusedError:
        print(f"\n[FAIL] Connection REFUSED on port {port}.")
        print("   Make sure TWS or IB Gateway is running and API is enabled:")
        print("   - TWS:  Edit > Global Configuration > API > Settings")
        print("   - IB Gateway:  Configure > Settings > API > Settings")
        print("   - Enable 'Enable ActiveX and Socket Clients'")
        print(f"   - Socket port must be {port}")
        print("   - Check 'Allow connections from localhost only'")
        return False
    except Exception as e:
        print(f"\n[FAIL] Connection failed: {e}")
        return False

    print("[OK] Connected to IBKR!\n")

    # Account info
    accounts = ib.managedAccounts()
    print(f"Managed Accounts: {accounts}")

    # Account summary
    summary = ib.accountSummary()
    key_tags = {
        "NetLiquidation": "Net Liquidation",
        "TotalCashValue": "Cash Balance",
        "BuyingPower": "Buying Power",
        "GrossPositionValue": "Positions Value",
    }
    print("\nAccount Summary:")
    for item in summary:
        if item.tag in key_tags:
            print(f"   {key_tags[item.tag]:20s}: ${float(item.value):>14,.2f} {item.currency}")

    # Positions
    positions = ib.positions()
    if positions:
        print(f"\nPositions ({len(positions)} total):")
        for pos in positions:
            print(f"   {pos.contract.symbol:8s} | {pos.position:>10.2f} shares | Avg Cost: ${pos.avgCost:>10.2f}")
    else:
        print("\nNo open positions.")

    ib.disconnect()
    print("\n[OK] Disconnected. Connection test PASSED.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test IBKR connection")
    parser.add_argument("--live", action="store_true", help="Connect to live trading (port 7496)")
    parser.add_argument("--port", type=int, help="Override port number")
    args = parser.parse_args()

    port = args.port or (7496 if args.live else 7497)
    mode = "LIVE" if port == 7496 else "PAPER"
    print(f"{'='*50}")
    print(f"  IBKR Connection Test -- {mode} TRADING")
    print(f"{'='*50}\n")

    success = test_connection(port=port)
    sys.exit(0 if success else 1)
