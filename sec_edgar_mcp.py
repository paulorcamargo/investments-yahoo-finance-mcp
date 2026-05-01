import asyncio
import json
import logging
import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sec_edgar_mcp")

# Create the MCP server
app = Server("SEC_EDGAR")

# ---------------------------------------------------------------------------
# Lazy import & identity setup for edgartools
# ---------------------------------------------------------------------------
_edgar_ready = False


def _ensure_edgar():
    """Import edgartools and set identity on first use."""
    global _edgar_ready
    if not _edgar_ready:
        import edgar
        # SEC requires a User-Agent with name + email
        edgar.set_identity("Paulo Camargo paulocamargo@hotmail.com")
        _edgar_ready = True


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
    return json.dumps(serialize(data), indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available SEC EDGAR tools."""
    return [
        types.Tool(
            name="edgar_search_company",
            description=(
                "Search SEC EDGAR for a company by ticker or CIK number. "
                "Returns company name, CIK, SIC code, and state of incorporation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'AAPL') or CIK number"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="edgar_get_filings",
            description=(
                "Get recent SEC filings for a company. Supports all filing types "
                "including 10-K (annual), 10-Q (quarterly), 8-K (current events), "
                "S-1 (IPO), 13F (institutional holdings), DEF 14A (proxy), etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')"
                    },
                    "form_type": {
                        "type": "string",
                        "description": (
                            "Filing type filter: '10-K', '10-Q', '8-K', '13F-HR', "
                            "'S-1', 'DEF 14A', '4' (insider), etc. Default: all types."
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of filings to return (max 20). Default: 5"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="edgar_get_financials",
            description=(
                "Extract structured financial statements from a company's latest "
                "10-K or 10-Q filing using XBRL. Returns income statement, balance "
                "sheet, or cash flow data in a structured format."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL')"
                    },
                    "statement_type": {
                        "type": "string",
                        "description": "'income', 'balance', or 'cashflow'. Default: 'income'"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="edgar_get_insider_transactions",
            description=(
                "Get recent insider trading transactions (Form 4 filings) for a "
                "company. Shows who bought/sold, how many shares, and at what price."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of transactions to return (max 20). Default: 10"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="edgar_get_company_facts",
            description=(
                "Get all XBRL facts reported by a company to the SEC. This is the "
                "raw structured data from all filings, useful for time-series analysis "
                "of specific metrics like Revenue, NetIncome, Assets, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL')"
                    },
                    "fact_name": {
                        "type": "string",
                        "description": (
                            "Specific XBRL fact to retrieve, e.g. 'Revenues', "
                            "'NetIncomeLoss', 'Assets', 'StockholdersEquity'. "
                            "If omitted, returns a list of all available facts."
                        )
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="edgar_full_text_search",
            description=(
                "Search across all SEC EDGAR filings using full-text search. "
                "Useful for finding specific disclosures, risk factors, or "
                "mentions of topics across multiple companies' filings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search text (e.g., 'artificial intelligence risk', 'supply chain disruption')"
                    },
                    "form_type": {
                        "type": "string",
                        "description": "Filter to a specific form type (e.g., '10-K', '8-K'). Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (max 20). Default: 5"
                    }
                },
                "required": ["query"]
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
        _ensure_edgar()
        import edgar

        result = None

        # ---- Search company ---------------------------------------------------
        if name == "edgar_search_company":
            query = arguments["query"].strip()
            company = edgar.Company(query)
            info = {
                "name": str(company.name),
                "cik": str(company.cik),
                "ticker": str(getattr(company, "tickers", query)),
                "sic": str(getattr(company, "sic", "N/A")),
                "sic_description": str(getattr(company, "sic_description", "N/A")),
                "state": str(getattr(company, "state_of_incorporation", "N/A")),
                "fiscal_year_end": str(getattr(company, "fiscal_year_end", "N/A")),
            }
            result = safe_json(info)

        # ---- Get filings ------------------------------------------------------
        elif name == "edgar_get_filings":
            ticker = arguments["ticker"].strip().upper()
            form_type = arguments.get("form_type")
            limit = min(arguments.get("limit", 5), 20)

            company = edgar.Company(ticker)
            filings = company.get_filings()

            if form_type:
                filings = filings.filter(form=form_type)

            entries = []
            for filing in filings[:limit]:
                entries.append({
                    "form": str(filing.form),
                    "filing_date": str(filing.filing_date),
                    "accession_number": str(filing.accession_no),
                    "description": str(getattr(filing, "description", "")),
                    "url": str(getattr(filing, "filing_url", "")),
                })
            result = safe_json(entries)

        # ---- Get financial statements -----------------------------------------
        elif name == "edgar_get_financials":
            ticker = arguments["ticker"].strip().upper()
            statement_type = arguments.get("statement_type", "income").lower()

            company = edgar.Company(ticker)
            financials = company.get_financials()

            if financials is None:
                result = f"No XBRL financial data found for {ticker}."
            else:
                if statement_type == "balance":
                    stmt = financials.balance_sheet
                elif statement_type == "cashflow":
                    stmt = financials.cash_flow_statement
                else:
                    stmt = financials.income_statement

                if stmt is not None:
                    if hasattr(stmt, "to_dataframe"):
                        df = stmt.to_dataframe()
                        result = df.to_json(indent=2)
                    elif hasattr(stmt, "to_dict"):
                        result = safe_json(stmt.to_dict())
                    else:
                        result = safe_json(str(stmt))
                else:
                    result = f"No {statement_type} statement found for {ticker}."

        # ---- Insider transactions ---------------------------------------------
        elif name == "edgar_get_insider_transactions":
            ticker = arguments["ticker"].strip().upper()
            limit = min(arguments.get("limit", 10), 20)

            company = edgar.Company(ticker)
            filings = company.get_filings().filter(form="4")

            entries = []
            for filing in filings[:limit]:
                entry = {
                    "form": "4",
                    "filing_date": str(filing.filing_date),
                    "accession_number": str(filing.accession_no),
                    "filer": str(getattr(filing, "filer", "N/A")),
                }
                # Try to parse the actual Form 4 document for transaction details
                try:
                    doc = filing.obj()
                    if hasattr(doc, "transactions"):
                        txns = []
                        for t in doc.transactions[:5]:
                            txns.append({
                                "security": str(getattr(t, "security_title", "")),
                                "transaction_type": str(getattr(t, "transaction_type", "")),
                                "shares": str(getattr(t, "shares", "")),
                                "price": str(getattr(t, "price", "")),
                                "date": str(getattr(t, "transaction_date", "")),
                            })
                        entry["transactions"] = txns
                    if hasattr(doc, "reporting_owner"):
                        entry["reporting_owner"] = str(doc.reporting_owner)
                except Exception:
                    pass  # Not all Form 4s parse cleanly
                entries.append(entry)
            result = safe_json(entries)

        # ---- Company facts (XBRL time-series) ---------------------------------
        elif name == "edgar_get_company_facts":
            ticker = arguments["ticker"].strip().upper()
            fact_name = arguments.get("fact_name")

            company = edgar.Company(ticker)
            facts = company.get_facts()

            if facts is None:
                result = f"No XBRL facts found for {ticker}."
            elif fact_name:
                # Try to find the specific fact
                if hasattr(facts, "to_pandas"):
                    df = facts.to_pandas()
                    # Filter for the requested fact
                    mask = df.index.get_level_values(0).str.contains(fact_name, case=False)
                    if mask.any():
                        filtered = df[mask]
                        result = filtered.head(40).to_json(indent=2)
                    else:
                        result = f"Fact '{fact_name}' not found. Use without fact_name to see available facts."
                else:
                    result = safe_json(str(facts))
            else:
                # Return list of available fact names
                if hasattr(facts, "to_pandas"):
                    df = facts.to_pandas()
                    fact_names = df.index.get_level_values(0).unique().tolist()[:100]
                    result = safe_json({"available_facts_sample": fact_names, "total": len(df.index.get_level_values(0).unique())})
                else:
                    result = safe_json(str(facts))

        # ---- Full-text search -------------------------------------------------
        elif name == "edgar_full_text_search":
            query = arguments["query"].strip()
            form_type = arguments.get("form_type")
            limit = min(arguments.get("limit", 5), 20)

            # edgartools supports efts (EDGAR Full-Text Search)
            if hasattr(edgar, "efts"):
                search_results = edgar.efts(query)
                entries = []
                count = 0
                for hit in search_results:
                    if form_type and str(getattr(hit, "form", "")).upper() != form_type.upper():
                        continue
                    entries.append({
                        "company": str(getattr(hit, "company_name", "")),
                        "ticker": str(getattr(hit, "ticker", "")),
                        "form": str(getattr(hit, "form", "")),
                        "filing_date": str(getattr(hit, "filing_date", "")),
                        "description": str(getattr(hit, "description", "")),
                    })
                    count += 1
                    if count >= limit:
                        break
                result = safe_json(entries)
            else:
                # Fallback: search via company filings
                result = safe_json({
                    "note": "Full-text search requires edgartools with EFTS support. "
                            "Please update edgartools to the latest version.",
                    "suggestion": "Use edgar_get_filings with a specific ticker instead."
                })

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
