import asyncio
import json
import logging
import datetime
from typing import Any

import mstarpy as ms
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("morningstar_mcp")

app = Server("Morningstar")

# Global session — Chrome opens once at startup, then all requests are plain HTTP
_session: ms.MorningstarSession | None = None


def get_session() -> ms.MorningstarSession:
    global _session
    if _session is None:
        logger.info("Initializing Morningstar session (Chrome will open briefly to capture auth token)...")
        _session = ms.MorningstarSession()
        logger.info("Morningstar session ready.")
    return _session


def serialize(obj):
    """Recursively convert non-JSON-serializable types."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(i) for i in obj]
    if hasattr(obj, "to_dict"):
        return serialize(obj.to_dict())
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return obj


def safe_json(data) -> str:
    return json.dumps(serialize(data), indent=2)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_security",
            description=(
                "Search Morningstar for a stock or fund by name, ticker, or ISIN. "
                "Returns SecId, name, ticker, and exchange for up to 5 matches."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Name, ticker, or ISIN to search for (e.g., 'AAPL', 'Apple', 'VTSAX')"
                    },
                    "security_type": {
                        "type": "string",
                        "description": "'stock' or 'fund'. Default: 'stock'"
                    }
                },
                "required": ["term"]
            }
        ),
        types.Tool(
            name="get_stock_overview",
            description="Get Morningstar overview for a stock: company profile, sector, industry, key executives.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name (e.g., 'AAPL', 'Microsoft')"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_analysis",
            description=(
                "Get Morningstar analyst data for a stock: star rating (1-5), fair value estimate, "
                "economic moat (none/narrow/wide), uncertainty rating, and analyst report summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_historical",
            description="Get historical OHLCV price and volume data for a stock from Morningstar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD. Default: 1 year ago"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD. Default: today"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_financials",
            description="Get financial statements for a stock from Morningstar (income statement, balance sheet, or cash flow).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"},
                    "statement_type": {
                        "type": "string",
                        "description": "'income', 'balance', or 'cashflow'. Default: 'income'"
                    },
                    "period": {
                        "type": "string",
                        "description": "'annual' or 'quarterly'. Default: 'annual'"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_valuation",
            description=(
                "Get Morningstar valuation metrics for a stock: price/fair value ratio, "
                "P/E, P/B, P/S, P/CF, and historical valuation data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_key_ratios",
            description=(
                "Get Morningstar key financial ratios for a stock: profitability, growth, "
                "financial leverage, and efficiency ratios over multiple years."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_ownership",
            description="Get institutional or mutual fund ownership for a stock from Morningstar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"},
                    "ownership_type": {
                        "type": "string",
                        "description": "'institution' or 'mutualfund'. Default: 'institution'"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_esg",
            description=(
                "Get ESG (Environmental, Social, Governance) risk data for a stock from Morningstar: "
                "ESG risk score, controversy level, carbon metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_stock_dividends",
            description="Get dividend payment history for a stock from Morningstar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker or company name"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_fund_overview",
            description=(
                "Get Morningstar fund overview: star rating (1-5), NAV, category, "
                "expense ratio, manager, inception date, and Morningstar analyst rating."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fund": {"type": "string", "description": "Fund ticker or fund name (e.g., 'VTSAX', 'SPY')"}
                },
                "required": ["fund"]
            }
        ),
        types.Tool(
            name="get_fund_holdings",
            description="Get top holdings of a mutual fund or ETF from Morningstar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund": {"type": "string", "description": "Fund ticker or fund name"}
                },
                "required": ["fund"]
            }
        ),
        types.Tool(
            name="get_fund_performance",
            description=(
                "Get fund trailing return performance from Morningstar: 1M, 3M, 6M, 1Y, 3Y, 5Y, 10Y "
                "returns vs. benchmark and category."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fund": {"type": "string", "description": "Fund ticker or fund name"}
                },
                "required": ["fund"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments")]

    try:
        session = get_session()
        result = None

        if name == "search_security":
            term = arguments.get("term", "").strip()
            sec_type = arguments.get("security_type", "stock").lower()
            fields = ["SecId", "Name", "Ticker", "ExchangeId"]
            if sec_type == "fund":
                funds = ms.Funds(term, session=session, pageSize=5)
                data = session.screener_universe(
                    term=term, language="en", field=fields, pageSize=5
                )
            else:
                data = session.screener_universe(
                    term=term,
                    language="en",
                    field=fields,
                    filters={"Universe": "e1,e10"},
                    pageSize=5
                )
            result = safe_json(data)

        elif name == "get_stock_overview":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.overview())

        elif name == "get_stock_analysis":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.analysisData())

        elif name == "get_stock_historical":
            ticker = arguments["ticker"].strip()
            today = datetime.date.today()
            start_dt = (
                datetime.date.fromisoformat(arguments["start_date"])
                if "start_date" in arguments
                else today - datetime.timedelta(days=365)
            )
            end_dt = (
                datetime.date.fromisoformat(arguments["end_date"])
                if "end_date" in arguments
                else today
            )
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.historical(start_dt, end_dt))

        elif name == "get_stock_financials":
            ticker = arguments["ticker"].strip()
            stmt_type = arguments.get("statement_type", "income").lower()
            period = arguments.get("period", "annual").lower()
            quarterly = period == "quarterly"
            stock = ms.Stock(ticker, session=session)
            if stmt_type == "balance":
                data = stock.balanceSheet(
                    period="Quarterly" if quarterly else "Annual",
                    reportType="Original"
                )
            elif stmt_type == "cashflow":
                data = stock.cashFlow(
                    period="Quarterly" if quarterly else "Annual",
                    reportType="Original"
                )
            else:
                data = stock.incomeStatement(
                    period="Quarterly" if quarterly else "Annual",
                    reportType="Original"
                )
            result = safe_json(data)

        elif name == "get_stock_valuation":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.valuation())

        elif name == "get_stock_key_ratios":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.keyRatio())

        elif name == "get_stock_ownership":
            ticker = arguments["ticker"].strip()
            ownership_type = arguments.get("ownership_type", "institution").lower()
            stock = ms.Stock(ticker, session=session)
            if ownership_type == "mutualfund":
                result = safe_json(stock.mutualFundOwnership())
            else:
                result = safe_json(stock.institutionOwnership())

        elif name == "get_stock_esg":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.esgRisk())

        elif name == "get_stock_dividends":
            ticker = arguments["ticker"].strip()
            stock = ms.Stock(ticker, session=session)
            result = safe_json(stock.dividends())

        elif name == "get_fund_overview":
            fund = arguments["fund"].strip()
            funds = ms.Funds(fund, session=session)
            result = safe_json(funds.quote())

        elif name == "get_fund_holdings":
            fund = arguments["fund"].strip()
            funds = ms.Funds(fund, session=session)
            holdings = funds.holdings()
            if hasattr(holdings, "to_json"):
                result = holdings.to_json(orient="records", indent=2)
            else:
                result = safe_json(holdings)

        elif name == "get_fund_performance":
            fund = arguments["fund"].strip()
            funds = ms.Funds(fund, session=session)
            result = safe_json(funds.trailingReturn())

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        return [types.TextContent(type="text", text=result or "No data returned.")]

    except Exception as e:
        logger.error("Error executing %s: %s", name, e)
        return [types.TextContent(type="text", text=f"Error executing {name}: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
