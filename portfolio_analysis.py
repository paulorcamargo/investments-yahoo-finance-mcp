import yfinance as yf
import pandas as pd

tickers_map = {
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
        results.append({
            "Holding": name,
            "Ticker": ticker,
            "Error": str(e)
        })

df = pd.DataFrame(results)
print(df.to_string())
