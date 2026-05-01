"""
Interactive Brokers (IBKR) MCP Server

Provides tools for accessing real-time market data, historical data,
fundamental analysis, and portfolio information via the IBKR TWS API.

Requirements:
  - An IBKR account (live or paper trading)
  - TWS or IB Gateway running with API enabled on port 7497 (paper) or 7496 (live)
  - pip install ib_insync mcp
"""

import asyncio

# Python 3.14 fix: create event loop before ib_insync/eventkit imports
# (Python 3.14 removed implicit loop creation in get_event_loop)
asyncio.set_event_loop(asyncio.new_event_loop())
import json
import logging
import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ibkr_mcp")

# Create the MCP server
app = Server("InteractiveBrokers")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IBKR_CONFIG = {
    "host": "127.0.0.1",
    "port": 7497,       # 7497 = Paper Trading, 7496 = Live Trading
    "client_id": 10,    # Unique client ID (avoid conflicts with other connections)
}

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_ib = None


def _get_ib():
    """Get or create an IB connection. Lazy-connect on first use."""
    global _ib
    from ib_insync import IB

    if _ib is None or not _ib.isConnected():
        _ib = IB()
        _ib.connect(
            IBKR_CONFIG["host"],
            IBKR_CONFIG["port"],
            clientId=IBKR_CONFIG["client_id"],
        )
        logger.info(
            "Connected to IBKR on %s:%s (clientId=%s)",
            IBKR_CONFIG["host"], IBKR_CONFIG["port"], IBKR_CONFIG["client_id"],
        )
    return _ib


def _make_contract(symbol: str, sec_type: str = "STK", exchange: str = "SMART",
                   currency: str = "USD"):
    """Create an IBKR contract object."""
    from ib_insync import Stock, Forex, Future, Option, Contract

    symbol = symbol.strip().upper()

    if sec_type.upper() == "FOREX":
        pair = symbol.replace("/", "")
        return Forex(pair)
    elif sec_type.upper() == "FUT":
        return Future(symbol, exchange=exchange, currency=currency)
    elif sec_type.upper() == "OPT":
        return Option(symbol, exchange=exchange, currency=currency)
    else:
        # STK covers stocks and ETFs
        return Stock(symbol, exchange, currency)


def serialize(obj):
    """Recursively convert non-JSON-serializable types."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(i) for i in obj]
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return serialize(vars(obj))
    if hasattr(obj, "tolist"):
        return obj.tolist()
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def safe_json(data) -> str:
    return json.dumps(serialize(data), indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available IBKR tools."""
    return [
        types.Tool(
            name="ibkr_get_quote",
            description=(
                "Get real-time market quote for a stock or ETF from Interactive Brokers. "
                "Returns bid, ask, last price, volume, high, low, open, close."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol (e.g., 'AAPL', 'SPY')"},
                    "exchange": {"type": "string", "description": "Exchange. Default: 'SMART' (best routing)"},
                    "currency": {"type": "string", "description": "Currency. Default: 'USD'. Use 'CAD' for TSX."},
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="ibkr_get_historical",
            description=(
                "Get historical OHLCV data from Interactive Brokers. Supports very granular "
                "intervals down to 1 second. More accurate than Yahoo Finance for intraday data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "duration": {
                        "type": "string",
                        "description": (
                            "How far back: '1 D' (1 day), '1 W' (week), '1 M' (month), "
                            "'3 M', '6 M', '1 Y', '2 Y'. Default: '1 M'"
                        ),
                    },
                    "bar_size": {
                        "type": "string",
                        "description": (
                            "Bar interval: '1 secs', '5 secs', '1 min', '5 mins', '15 mins', "
                            "'30 mins', '1 hour', '4 hours', '1 day', '1 week', '1 month'. "
                            "Default: '1 day'"
                        ),
                    },
                    "exchange": {"type": "string", "description": "Default: 'SMART'"},
                    "currency": {"type": "string", "description": "Default: 'USD'"},
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="ibkr_get_fundamentals",
            description=(
                "Get fundamental data for a stock from Interactive Brokers (Reuters Fundamentals). "
                "Includes financial statements, ratios, earnings estimates, and company overview. "
                "More detailed than Yahoo Finance fundamentals."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "report_type": {
                        "type": "string",
                        "description": (
                            "Type of fundamental report: "
                            "'ReportsFinSummary' (financial summary), "
                            "'ReportsOwnership' (ownership), "
                            "'ReportSnapshot' (company snapshot/overview), "
                            "'ReportsFinStatements' (detailed financial statements), "
                            "'RESC' (analyst estimates & consensus). "
                            "Default: 'ReportSnapshot'"
                        ),
                    },
                    "exchange": {"type": "string", "description": "Default: 'SMART'"},
                    "currency": {"type": "string", "description": "Default: 'USD'"},
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="ibkr_get_contract_details",
            description=(
                "Get detailed contract information for a stock, ETF, future, or option. "
                "Returns trading hours, tick sizes, margin requirements, industry/category, "
                "and other exchange-specific details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "sec_type": {
                        "type": "string",
                        "description": "'STK' (stock/ETF), 'FUT' (future), 'OPT' (option), 'FOREX'. Default: 'STK'",
                    },
                    "exchange": {"type": "string", "description": "Default: 'SMART'"},
                    "currency": {"type": "string", "description": "Default: 'USD'"},
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="ibkr_get_portfolio",
            description=(
                "Get your current IBKR portfolio positions. Shows all holdings with "
                "market value, average cost, unrealized P&L, and realized P&L."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="ibkr_get_account_summary",
            description=(
                "Get your IBKR account summary: net liquidation value, buying power, "
                "cash balance, total positions value, margin used, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="ibkr_market_scanner",
            description=(
                "Run an IBKR market scanner to find stocks matching specific criteria. "
                "Examples: most active, top gainers, top losers, high dividend yield, "
                "hot by volume, top % gainers, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_code": {
                        "type": "string",
                        "description": (
                            "Scanner type: 'MOST_ACTIVE', 'TOP_PERC_GAIN', 'TOP_PERC_LOSE', "
                            "'HOT_BY_VOLUME', 'HIGH_DIVIDEND_YIELD_IB', 'TOP_OPEN_PERC_GAIN', "
                            "'TOP_OPEN_PERC_LOSE', 'TOP_AFTER_HOURS_PERC_GAIN', "
                            "'HIGH_VS_13W_HL', 'LOW_VS_13W_HL', 'HIGH_VS_52W_HL', "
                            "'LOW_VS_52W_HL'. Default: 'MOST_ACTIVE'"
                        ),
                    },
                    "instrument": {
                        "type": "string",
                        "description": "'STK' (stocks), 'ETF.EQ.US' (US ETFs). Default: 'STK'",
                    },
                    "location": {
                        "type": "string",
                        "description": (
                            "'STK.US.MAJOR' (US major), 'STK.US' (all US), 'STK.NA' (North America), "
                            "'STK.WORLD' (global). Default: 'STK.US.MAJOR'"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (max 50). Default: 15",
                    },
                },
            },
        ),
        types.Tool(
            name="ibkr_get_news",
            description=(
                "Get recent news headlines for a stock from IBKR's news feed. "
                "Sources include Reuters, Dow Jones, Benzinga, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "limit": {"type": "integer", "description": "Number of headlines (max 20). Default: 10"},
                    "exchange": {"type": "string", "description": "Default: 'SMART'"},
                    "currency": {"type": "string", "description": "Default: 'USD'"},
                },
                "required": ["symbol"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool execution requests."""
    if arguments is None:
        arguments = {}

    try:
        from ib_insync import ScannerSubscription

        ib = _get_ib()
        result = None

        # ---- Real-time quote ------------------------------------------------
        if name == "ibkr_get_quote":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange", "SMART")
            currency = arguments.get("currency", "USD")

            contract = _make_contract(symbol, "STK", exchange, currency)
            ib.qualifyContracts(contract)

            ticker = ib.reqMktData(contract, "", False, False)
            await asyncio.sleep(2)  # Wait for data to arrive

            data = {
                "symbol": symbol.upper(),
                "bid": ticker.bid,
                "ask": ticker.ask,
                "last": ticker.last,
                "volume": ticker.volume,
                "high": ticker.high,
                "low": ticker.low,
                "open": ticker.open,
                "close": ticker.close,
                "halted": ticker.halted,
            }
            ib.cancelMktData(contract)
            result = safe_json(data)

        # ---- Historical data -------------------------------------------------
        elif name == "ibkr_get_historical":
            symbol = arguments["symbol"]
            duration = arguments.get("duration", "1 M")
            bar_size = arguments.get("bar_size", "1 day")
            exchange = arguments.get("exchange", "SMART")
            currency = arguments.get("currency", "USD")

            contract = _make_contract(symbol, "STK", exchange, currency)
            ib.qualifyContracts(contract)

            bars = ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )

            data = []
            for bar in bars:
                data.append({
                    "date": str(bar.date),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "average": bar.average,
                    "barCount": bar.barCount,
                })
            result = safe_json({"symbol": symbol.upper(), "bars": data})

        # ---- Fundamental data ------------------------------------------------
        elif name == "ibkr_get_fundamentals":
            symbol = arguments["symbol"]
            report_type = arguments.get("report_type", "ReportSnapshot")
            exchange = arguments.get("exchange", "SMART")
            currency = arguments.get("currency", "USD")

            contract = _make_contract(symbol, "STK", exchange, currency)
            ib.qualifyContracts(contract)

            report = ib.reqFundamentalData(contract, report_type)
            if report:
                # Reports come as XML; return as-is for parsing
                result = json.dumps({
                    "symbol": symbol.upper(),
                    "report_type": report_type,
                    "data": report[:10000],  # Truncate very long reports
                }, indent=2)
            else:
                result = f"No fundamental data returned for {symbol} (report: {report_type})."

        # ---- Contract details ------------------------------------------------
        elif name == "ibkr_get_contract_details":
            symbol = arguments["symbol"]
            sec_type = arguments.get("sec_type", "STK")
            exchange = arguments.get("exchange", "SMART")
            currency = arguments.get("currency", "USD")

            contract = _make_contract(symbol, sec_type, exchange, currency)
            details_list = ib.reqContractDetails(contract)

            data = []
            for d in details_list[:5]:  # Limit to 5 results
                data.append({
                    "symbol": d.contract.symbol,
                    "secType": d.contract.secType,
                    "exchange": d.contract.exchange,
                    "currency": d.contract.currency,
                    "longName": d.longName,
                    "industry": d.industry,
                    "category": d.category,
                    "subcategory": d.subcategory,
                    "marketName": d.marketName,
                    "minTick": d.minTick,
                    "tradingHours": d.tradingHours[:200] if d.tradingHours else None,
                    "liquidHours": d.liquidHours[:200] if d.liquidHours else None,
                })
            result = safe_json(data)

        # ---- Portfolio positions ---------------------------------------------
        elif name == "ibkr_get_portfolio":
            positions = ib.positions()

            data = []
            for pos in positions:
                data.append({
                    "symbol": pos.contract.symbol,
                    "secType": pos.contract.secType,
                    "exchange": pos.contract.exchange,
                    "currency": pos.contract.currency,
                    "position": pos.position,
                    "avgCost": pos.avgCost,
                    "account": pos.account,
                })

            # Also get portfolio items with P&L
            ib.reqAccountUpdates(True, "")
            await asyncio.sleep(2)
            portfolio = ib.portfolio()
            pnl_data = []
            for item in portfolio:
                pnl_data.append({
                    "symbol": item.contract.symbol,
                    "position": item.position,
                    "marketPrice": item.marketPrice,
                    "marketValue": item.marketValue,
                    "averageCost": item.averageCost,
                    "unrealizedPNL": item.unrealizedPNL,
                    "realizedPNL": item.realizedPNL,
                })
            ib.reqAccountUpdates(False, "")

            result = safe_json({"positions": data, "portfolio_pnl": pnl_data})

        # ---- Account summary -------------------------------------------------
        elif name == "ibkr_get_account_summary":
            summary = ib.accountSummary()

            data = {}
            for item in summary:
                data[item.tag] = {
                    "value": item.value,
                    "currency": item.currency,
                    "account": item.account,
                }
            result = safe_json(data)

        # ---- Market scanner --------------------------------------------------
        elif name == "ibkr_market_scanner":
            scan_code = arguments.get("scan_code", "MOST_ACTIVE")
            instrument = arguments.get("instrument", "STK")
            location = arguments.get("location", "STK.US.MAJOR")
            limit = min(arguments.get("limit", 15), 50)

            sub = ScannerSubscription(
                instrument=instrument,
                locationCode=location,
                scanCode=scan_code,
                numberOfRows=limit,
            )

            results_list = ib.reqScannerData(sub)

            data = []
            for rank, item in enumerate(results_list, 1):
                data.append({
                    "rank": rank,
                    "symbol": item.contractDetails.contract.symbol,
                    "secType": item.contractDetails.contract.secType,
                    "exchange": item.contractDetails.contract.primaryExchange,
                    "longName": item.contractDetails.longName,
                    "distance": item.distance,
                    "benchmark": item.benchmark,
                    "projection": item.projection,
                    "legsStr": item.legsStr,
                })
            result = safe_json({"scan_code": scan_code, "results": data})

        # ---- News headlines --------------------------------------------------
        elif name == "ibkr_get_news":
            symbol = arguments["symbol"]
            limit = min(arguments.get("limit", 10), 20)
            exchange = arguments.get("exchange", "SMART")
            currency = arguments.get("currency", "USD")

            contract = _make_contract(symbol, "STK", exchange, currency)
            ib.qualifyContracts(contract)

            headlines = ib.reqHistoricalNews(
                contract.conId, "", "", limit,
                providerCodes="BZ+DJNL+BRFG+BRFUPDN+DJ-N+DJ-RT",
            )

            data = []
            for h in headlines:
                data.append({
                    "time": str(h.time),
                    "providerCode": h.providerCode,
                    "articleId": h.articleId,
                    "headline": h.headline,
                })
            result = safe_json({"symbol": symbol.upper(), "headlines": data})

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        if result is None:
            result = "No data returned."
        return [types.TextContent(type="text", text=result)]

    except ConnectionRefusedError:
        msg = (
            "Cannot connect to IBKR TWS/Gateway. Please ensure:\n"
            "1. TWS or IB Gateway is running\n"
            "2. API is enabled (Edit → Global Configuration → API → Settings)\n"
            "3. Socket port matches (default: 7497 for Paper, 7496 for Live)\n"
            "4. 'Allow connections from localhost' is checked"
        )
        logger.error(msg)
        return [types.TextContent(type="text", text=msg)]

    except Exception as e:
        logger.error("Error executing %s: %s", name, e, exc_info=True)
        return [types.TextContent(type="text", text=f"Error executing {name}: {e}")]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
