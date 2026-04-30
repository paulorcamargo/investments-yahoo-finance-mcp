import asyncio
import json
import logging
from typing import Any, Sequence

import yfinance as yf
import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yahoo_finance_mcp")

# Create the MCP server
app = Server("YahooFinance")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_ticker_info",
            description="Get general information about a company by its ticker symbol. Includes company description, sector, metrics like PE ratio, dividend yield, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_historical_data",
            description="Get historical market data for a ticker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "description": "Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max). Default 1mo"},
                    "interval": {"type": "string", "description": "Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo). Default 1d"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_financial_statements",
            description="Get financial statements for a ticker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "statement_type": {"type": "string", "description": "income, balance, or cashflow. Default is income."}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_news",
            description="Get recent news articles for a ticker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_options_chain",
            description="Get options chain for a ticker. Returns expiration dates if no date is provided.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "date": {"type": "string", "description": "Expiration date in YYYY-MM-DD format (optional)"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_analyst_recommendations",
            description="Get analyst recommendations and price targets for a ticker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_institutional_holders",
            description="Get institutional holders for a ticker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["ticker"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool execution requests."""
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments")]
        
    ticker = arguments.get("ticker")
    if not ticker:
        return [types.TextContent(type="text", text="Missing required argument 'ticker'")]

    try:
        if name == "get_ticker_info":
            stock = yf.Ticker(ticker)
            info = stock.info
            result = json.dumps(info, indent=2)
            
        elif name == "get_historical_data":
            period = arguments.get("period", "1mo")
            interval = arguments.get("interval", "1d")
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            if hist.empty:
                result = f"No historical data found for {ticker}."
            else:
                hist = hist.reset_index()
                if 'Date' in hist.columns:
                    hist['Date'] = hist['Date'].astype(str)
                elif 'Datetime' in hist.columns:
                    hist['Datetime'] = hist['Datetime'].astype(str)
                result = hist.to_json(orient="records", indent=2)

        elif name == "get_financial_statements":
            statement_type = arguments.get("statement_type", "income")
            stock = yf.Ticker(ticker)
            if statement_type.lower() == "income":
                data = stock.financials
            elif statement_type.lower() == "balance":
                data = stock.balance_sheet
            elif statement_type.lower() == "cashflow":
                data = stock.cashflow
            else:
                result = "Invalid statement_type. Use 'income', 'balance', or 'cashflow'."
                return [types.TextContent(type="text", text=result)]
                
            if data is None or data.empty:
                result = f"No {statement_type} data found for {ticker}."
            else:
                data.columns = [col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col) for col in data.columns]
                result = data.to_json(indent=2)

        elif name == "get_news":
            stock = yf.Ticker(ticker)
            news = stock.news
            result = json.dumps(news, indent=2)

        elif name == "get_options_chain":
            date = arguments.get("date")
            stock = yf.Ticker(ticker)
            expirations = stock.options
            if not expirations:
                result = f"No options data found for {ticker}."
            elif not date:
                result = json.dumps({"expiration_dates": list(expirations)}, indent=2)
            elif date not in expirations:
                result = f"Invalid date. Available expirations: {expirations}"
            else:
                opt = stock.option_chain(date)
                calls = opt.calls.copy()
                puts = opt.puts.copy()
                for df in [calls, puts]:
                    if 'lastTradeDate' in df.columns:
                        df['lastTradeDate'] = df['lastTradeDate'].astype(str)
                result = json.dumps({
                    "calls": json.loads(calls.to_json(orient="records")),
                    "puts": json.loads(puts.to_json(orient="records"))
                }, indent=2)

        elif name == "get_analyst_recommendations":
            stock = yf.Ticker(ticker)
            recs = stock.recommendations
            if recs is None or recs.empty:
                result = f"No analyst recommendations found for {ticker}."
            else:
                result = recs.to_json(orient="records", indent=2)

        elif name == "get_institutional_holders":
            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders
            if holders is None or holders.empty:
                result = f"No institutional holders data found for {ticker}."
            else:
                if 'Date Reported' in holders.columns:
                    holders['Date Reported'] = holders['Date Reported'].astype(str)
                result = holders.to_json(orient="records", indent=2)
                
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [types.TextContent(type="text", text=f"Error executing {name}: {e}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
