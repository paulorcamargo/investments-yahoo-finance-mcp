import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tradingview_mcp")

# Create the MCP server
app = Server("TradingView")

# ---------------------------------------------------------------------------
# Mapping helpers for TradingView screeners & exchanges
# ---------------------------------------------------------------------------
# Common exchange mappings — tradingview-ta requires the correct screener + exchange
EXCHANGE_MAP = {
    # US markets
    "NASDAQ": "america",
    "NYSE": "america",
    "AMEX": "america",
    # Canadian markets
    "TSX": "canada",
    "TSXV": "canada",
    "CSE": "canada",
    "NEO": "canada",
    # International
    "LSE": "uk",
    "XETRA": "germany",
    "EURONEXT": "france",
    "ASX": "australia",
    "NSE": "india",
    "BSE": "india",
    "HKEX": "hongkong",
    "TSE": "japan",
    "SSE": "china",
    "SZSE": "china",
    "KRX": "korea",
    "BOVESPA": "brazil",
    "BMV": "mexico",
    # Crypto
    "BINANCE": "crypto",
    "COINBASE": "crypto",
    "BYBIT": "crypto",
    "KRAKEN": "crypto",
    # Forex
    "FX_IDC": "forex",
    "OANDA": "forex",
    "FOREX": "forex",
}

# Default US exchanges to try when user doesn't specify
DEFAULT_US_EXCHANGES = ["NASDAQ", "NYSE", "AMEX"]

# Interval display names
INTERVAL_NAMES = {
    "1m": "1 Minute",
    "5m": "5 Minutes",
    "15m": "15 Minutes",
    "30m": "30 Minutes",
    "1h": "1 Hour",
    "2h": "2 Hours",
    "4h": "4 Hours",
    "1d": "1 Day",
    "1W": "1 Week",
    "1M": "1 Month",
}


def _get_analysis(symbol: str, exchange: str | None, screener: str | None, interval: str):
    """Create a TA_Handler and fetch analysis. Auto-detects exchange if not specified."""
    from tradingview_ta import TA_Handler, Interval

    interval_map = {
        "1m": Interval.INTERVAL_1_MINUTE,
        "5m": Interval.INTERVAL_5_MINUTES,
        "15m": Interval.INTERVAL_15_MINUTES,
        "30m": Interval.INTERVAL_30_MINUTES,
        "1h": Interval.INTERVAL_1_HOUR,
        "2h": Interval.INTERVAL_2_HOURS,
        "4h": Interval.INTERVAL_4_HOURS,
        "1d": Interval.INTERVAL_1_DAY,
        "1W": Interval.INTERVAL_1_WEEK,
        "1M": Interval.INTERVAL_1_MONTH,
    }

    tv_interval = interval_map.get(interval, Interval.INTERVAL_1_DAY)
    symbol = symbol.upper().strip()

    # If exchange and screener provided, use them directly
    if exchange and screener:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener.lower(),
            exchange=exchange.upper(),
            interval=tv_interval,
        )
        return handler.get_analysis()

    # If exchange provided, look up screener
    if exchange:
        scr = EXCHANGE_MAP.get(exchange.upper(), "america")
        handler = TA_Handler(
            symbol=symbol,
            screener=scr,
            exchange=exchange.upper(),
            interval=tv_interval,
        )
        return handler.get_analysis()

    # Auto-detect: try common US exchanges
    last_err = None
    for exch in DEFAULT_US_EXCHANGES:
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="america",
                exchange=exch,
                interval=tv_interval,
            )
            return handler.get_analysis()
        except Exception as e:
            last_err = e
            continue

    # Try TSX for Canadian tickers
    for exch in ["TSX", "TSXV"]:
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="canada",
                exchange=exch,
                interval=tv_interval,
            )
            return handler.get_analysis()
        except Exception:
            continue

    raise last_err or Exception(f"Could not find {symbol} on any supported exchange.")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available TradingView technical analysis tools."""
    return [
        types.Tool(
            name="tv_get_analysis",
            description=(
                "Get TradingView's complete technical analysis for a ticker: "
                "overall recommendation (STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL), "
                "oscillator summary, moving average summary, and detailed indicator values "
                "(RSI, MACD, Stochastic, ADX, CCI, Bollinger Bands, Ichimoku, etc.). "
                "Supports multiple timeframes from 1-minute to monthly."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'AAPL', 'MSFT', 'BTCUSD')"
                    },
                    "exchange": {
                        "type": "string",
                        "description": (
                            "Exchange name: NASDAQ, NYSE, AMEX, TSX, LSE, BINANCE, etc. "
                            "Auto-detected for US stocks if omitted."
                        )
                    },
                    "screener": {
                        "type": "string",
                        "description": (
                            "Market screener: 'america', 'canada', 'uk', 'crypto', 'forex', etc. "
                            "Auto-detected from exchange if omitted."
                        )
                    },
                    "interval": {
                        "type": "string",
                        "description": (
                            "Analysis timeframe: '1m', '5m', '15m', '30m', '1h', '2h', '4h', "
                            "'1d', '1W', '1M'. Default: '1d' (daily)."
                        )
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="tv_get_summary",
            description=(
                "Get a concise TradingView buy/sell summary for a ticker. "
                "Returns the overall recommendation plus oscillator and moving average "
                "signal counts (how many say BUY, SELL, or NEUTRAL)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'AAPL', 'RY')"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name (optional, auto-detected for US/CA)"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Timeframe: '1m','5m','15m','30m','1h','2h','4h','1d','1W','1M'. Default: '1d'"
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="tv_multi_timeframe",
            description=(
                "Get TradingView analysis across multiple timeframes simultaneously. "
                "Shows the recommendation (BUY/SELL/NEUTRAL) for 15m, 1h, 4h, 1d, and 1W "
                "so you can see alignment or divergence across timeframes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'AAPL')"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name (optional, auto-detected for US/CA)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="tv_get_indicators",
            description=(
                "Get specific technical indicator values from TradingView. "
                "Returns raw values for RSI, MACD, Stochastic, ADX, CCI, ATR, "
                "Bollinger Bands, moving averages (SMA/EMA 10, 20, 50, 100, 200), "
                "Ichimoku, Williams %R, Ultimate Oscillator, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'AAPL')"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name (optional, auto-detected)"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Timeframe. Default: '1d'"
                    },
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of specific indicator keys to return. "
                            "Examples: 'RSI', 'MACD.macd', 'MACD.signal', 'Stoch.K', "
                            "'Stoch.D', 'ADX', 'CCI20', 'ATR', 'BB.upper', 'BB.lower', "
                            "'SMA10', 'SMA20', 'SMA50', 'SMA200', 'EMA10', 'EMA20', "
                            "'EMA50', 'EMA200', 'Ichimoku.BLine', 'W.R', 'UO', 'close', "
                            "'volume', 'open', 'high', 'low'. "
                            "If omitted, returns all available indicators."
                        )
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="tv_compare_tickers",
            description=(
                "Compare TradingView technical analysis for multiple tickers side-by-side. "
                "Shows the recommendation, RSI, MACD, and moving average signals for each. "
                "Useful for comparing stocks in the same sector or screening candidates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ticker symbols to compare (max 10)"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange for all tickers (optional, auto-detected)"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Timeframe. Default: '1d'"
                    }
                },
                "required": ["symbols"]
            }
        ),
    ]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool execution requests."""
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments")]

    try:
        result = None

        # ---- Full analysis ------------------------------------------------
        if name == "tv_get_analysis":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange")
            screener = arguments.get("screener")
            interval = arguments.get("interval", "1d")

            analysis = _get_analysis(symbol, exchange, screener, interval)

            data = {
                "symbol": symbol.upper(),
                "interval": INTERVAL_NAMES.get(interval, interval),
                "recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
                "summary": {
                    "overall": analysis.summary,
                },
                "oscillators": analysis.oscillators,
                "moving_averages": analysis.moving_averages,
                "indicators": analysis.indicators,
            }
            result = json.dumps(data, indent=2, default=str)

        # ---- Quick summary -------------------------------------------------
        elif name == "tv_get_summary":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange")
            interval = arguments.get("interval", "1d")

            analysis = _get_analysis(symbol, exchange, None, interval)

            data = {
                "symbol": symbol.upper(),
                "interval": INTERVAL_NAMES.get(interval, interval),
                "overall_recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
                "buy_signals": analysis.summary.get("BUY", 0),
                "sell_signals": analysis.summary.get("SELL", 0),
                "neutral_signals": analysis.summary.get("NEUTRAL", 0),
                "oscillators_recommendation": analysis.oscillators.get("RECOMMENDATION", "N/A"),
                "moving_averages_recommendation": analysis.moving_averages.get("RECOMMENDATION", "N/A"),
            }
            result = json.dumps(data, indent=2)

        # ---- Multi-timeframe ------------------------------------------------
        elif name == "tv_multi_timeframe":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange")

            timeframes = ["15m", "1h", "4h", "1d", "1W"]
            results_list = []

            for tf in timeframes:
                try:
                    analysis = _get_analysis(symbol, exchange, None, tf)
                    results_list.append({
                        "timeframe": INTERVAL_NAMES.get(tf, tf),
                        "recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
                        "buy": analysis.summary.get("BUY", 0),
                        "sell": analysis.summary.get("SELL", 0),
                        "neutral": analysis.summary.get("NEUTRAL", 0),
                        "rsi": round(analysis.indicators.get("RSI", 0) or 0, 2),
                    })
                except Exception as e:
                    results_list.append({
                        "timeframe": INTERVAL_NAMES.get(tf, tf),
                        "error": str(e)
                    })

            data = {
                "symbol": symbol.upper(),
                "timeframe_analysis": results_list,
            }
            result = json.dumps(data, indent=2)

        # ---- Raw indicators --------------------------------------------------
        elif name == "tv_get_indicators":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange")
            interval = arguments.get("interval", "1d")
            requested = arguments.get("indicators")

            analysis = _get_analysis(symbol, exchange, None, interval)

            if requested:
                indicators = {k: analysis.indicators.get(k) for k in requested}
            else:
                indicators = analysis.indicators

            data = {
                "symbol": symbol.upper(),
                "interval": INTERVAL_NAMES.get(interval, interval),
                "indicators": indicators,
            }
            result = json.dumps(data, indent=2, default=str)

        # ---- Compare tickers -------------------------------------------------
        elif name == "tv_compare_tickers":
            symbols = arguments["symbols"][:10]
            exchange = arguments.get("exchange")
            interval = arguments.get("interval", "1d")

            comparisons = []
            for sym in symbols:
                try:
                    analysis = _get_analysis(sym, exchange, None, interval)
                    comparisons.append({
                        "symbol": sym.upper(),
                        "recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
                        "buy_signals": analysis.summary.get("BUY", 0),
                        "sell_signals": analysis.summary.get("SELL", 0),
                        "rsi": round(analysis.indicators.get("RSI", 0) or 0, 2),
                        "macd": round(analysis.indicators.get("MACD.macd", 0) or 0, 4),
                        "adx": round(analysis.indicators.get("ADX", 0) or 0, 2),
                        "sma20": round(analysis.indicators.get("SMA20", 0) or 0, 2),
                        "sma50": round(analysis.indicators.get("SMA50", 0) or 0, 2),
                        "sma200": round(analysis.indicators.get("SMA200", 0) or 0, 2),
                        "close": round(analysis.indicators.get("close", 0) or 0, 2),
                    })
                except Exception as e:
                    comparisons.append({
                        "symbol": sym.upper(),
                        "error": str(e)
                    })

            data = {
                "interval": INTERVAL_NAMES.get(interval, interval),
                "comparison": comparisons,
            }
            result = json.dumps(data, indent=2)

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        if result is None:
            result = "No data returned."
        return [types.TextContent(type="text", text=result)]

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
