import logging
import yfinance as yf
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TICKERS_MAP = {
    "META": "META",
    "RY": "RY.TO",
    "SIRI": "SIRI",
    "MSFT": "MSFT",
    "STZ": "STZ",
    "FSZ": "FSZ.TO",
    "ORCL": "ORCL",
    "KULR": "KULR",
    "VCN": "VCN.TO",
    "XAW": "XAW.TO",
    "QQQ": "QQQ",
    "ZEA": "ZEA.TO",
    "XIT": "XIT.TO"
}


def analyze_portfolio(tickers_map: dict) -> pd.DataFrame:
    results = []
    for name, ticker in tickers_map.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            reco = info.get("recommendationKey", "N/A")
            target = info.get("targetMeanPrice", 0)
            price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            upside = ((target / price) - 1) * 100 if price and target else 0

            results.append({
                "Holding": name,
                "Ticker": ticker,
                "Price": price,
                "Target": target,
                "Upside %": round(upside, 2),
                "Recommendation": reco
            })
        except Exception as e:
            logger.warning("Failed to fetch %s (%s): %s", name, ticker, e)
            results.append({
                "Holding": name,
                "Ticker": ticker,
                "Price": None,
                "Target": None,
                "Upside %": None,
                "Recommendation": "ERROR"
            })

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = analyze_portfolio(TICKERS_MAP)
    print(df.to_string())
