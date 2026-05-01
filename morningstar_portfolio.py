import logging
import mstarpy as ms
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Map display name → ticker as recognized by Morningstar
TICKERS_MAP = {
    "META": "META",
    "RY": "RY",
    "SIRI": "SIRI",
    "MSFT": "MSFT",
    "STZ": "STZ",
    "FSZ": "FSZ",
    "ORCL": "ORCL",
    "KULR": "KULR",
    "VCN": "VCN",
    "XAW": "XAW",
    "QQQ": "QQQ",
    "ZEA": "ZEA",
    "XIT": "XIT",
}


def analyze_holding(name: str, ticker: str, session: ms.MorningstarSession) -> dict:
    try:
        stock = ms.Stock(ticker, session=session)
        data = stock.analysisData()

        star_rating = data.get("starRating")
        fair_value = data.get("fairValue")
        price = data.get("lastPrice") or data.get("price")
        moat = data.get("moat", {}).get("moatTrend") or data.get("economicMoat", "N/A")
        uncertainty = data.get("uncertainty", "N/A")

        upside = ((fair_value / price) - 1) * 100 if fair_value and price else None
        stars = "★" * int(star_rating) + "☆" * (5 - int(star_rating)) if star_rating else "N/A"

        return {
            "Holding": name,
            "Ticker": ticker,
            "Price": round(price, 2) if price else None,
            "Fair Value": round(fair_value, 2) if fair_value else None,
            "Upside %": round(upside, 2) if upside is not None else None,
            "Star Rating": stars,
            "Stars": star_rating or 0,
            "Economic Moat": moat.capitalize() if isinstance(moat, str) else "N/A",
            "Uncertainty": uncertainty or "N/A",
        }
    except Exception as e:
        logger.warning("Failed to fetch %s (%s): %s", name, ticker, e)
        return {
            "Holding": name,
            "Ticker": ticker,
            "Price": None,
            "Fair Value": None,
            "Upside %": None,
            "Star Rating": "ERROR",
            "Stars": 0,
            "Economic Moat": "N/A",
            "Uncertainty": "N/A",
        }


def analyze_portfolio(tickers_map: dict) -> pd.DataFrame:
    print("Initializing Morningstar session (Chrome will open briefly)...")
    session = ms.MorningstarSession()
    print("Session ready.\n")

    results = [analyze_holding(name, ticker, session) for name, ticker in tickers_map.items()]
    df = pd.DataFrame(results).sort_values("Stars", ascending=False)
    return df.drop(columns=["Stars"])


if __name__ == "__main__":
    df = analyze_portfolio(TICKERS_MAP)
    print(df.to_string(index=False))
