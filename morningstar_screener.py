import concurrent.futures
import logging
import requests
import pandas as pd
import mstarpy as ms

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_sp500_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    df = pd.read_html(response.text, flavor="html5lib")[0]
    return df["Symbol"].str.replace(".", "-", regex=False).tolist()


def analyze_ticker(ticker: str, session: ms.MorningstarSession) -> dict | None:
    try:
        stock = ms.Stock(ticker, session=session)
        data = stock.analysisData()

        # Extract key Morningstar metrics
        star_rating = data.get("starRating")
        fair_value = data.get("fairValue")
        moat = data.get("moat", {}).get("moatTrend") or data.get("economicMoat")
        uncertainty = data.get("uncertainty")
        price = data.get("lastPrice") or data.get("price")
        name = data.get("companyName") or ticker

        if not star_rating or not fair_value or not price:
            return None

        discount = (fair_value - price) / fair_value  # positive = discount, negative = premium

        # Criteria:
        # 1. Morningstar Star Rating >= 4 (4 or 5 stars = undervalued)
        # 2. Discount to fair value >= 15%
        # 3. Economic moat is narrow or wide (quality filter)
        if (
            star_rating >= 4
            and discount >= 0.15
            and moat in ("narrow", "wide")
        ):
            return {
                "Ticker": ticker,
                "Name": name,
                "Star Rating": f"{'★' * int(star_rating)}{'☆' * (5 - int(star_rating))}",
                "Stars": star_rating,
                "Price": round(price, 2),
                "Fair Value": round(fair_value, 2),
                "Discount to FV": f"{discount * 100:.1f}%",
                "Economic Moat": moat.capitalize() if moat else "N/A",
                "Uncertainty": uncertainty or "N/A",
            }
    except Exception as e:
        logger.debug("Skipping %s: %s", ticker, e)
    return None


def main():
    print("Initializing Morningstar session (Chrome will open briefly)...")
    session = ms.MorningstarSession()
    print("Session ready.\n")

    print("Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers. Screening with Morningstar ratings...\n")

    results = []
    # Use threads — after Selenium init, all mstarpy calls are plain HTTP
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(analyze_ticker, t, session): t for t in tickers}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            if i % 50 == 0:
                logger.info("Progress: %d / %d", i, len(tickers))
            res = future.result()
            if res:
                results.append(res)

    results.sort(key=lambda x: (x["Stars"], float(x["Discount to FV"].strip("%"))), reverse=True)

    df = pd.DataFrame(results)
    print("\n--- MORNINGSTAR SCREENER RESULTS ---")
    if df.empty:
        print("No stocks found matching criteria (4-5 stars, ≥15% discount to fair value, narrow/wide moat).")
    else:
        print(df.drop(columns=["Stars"]).to_string(index=False))

    df.to_csv("morningstar_screener_results.csv", index=False)
    print("\nSaved to morningstar_screener_results.csv")


if __name__ == "__main__":
    main()
