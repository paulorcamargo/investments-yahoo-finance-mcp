import yfinance as yf
import pandas as pd
import concurrent.futures
import json
import urllib.request
from bs4 import BeautifulSoup

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, verify=False)
    tables = pd.read_html(response.text, flavor='html5lib')
    df = tables[0]
    tickers = df['Symbol'].tolist()
    # Handle BRK.B -> BRK-B for yfinance
    tickers = [t.replace('.', '-') for t in tickers]
    return tickers

def analyze_ticker(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice'))
        low_52week = info.get('fiftyTwoWeekLow')
        recommendation = info.get('recommendationKey')
        target_price = info.get('targetMeanPrice')
        
        if not current_price or not low_52week or not target_price:
            return None
            
        # Criteria:
        # 1. Close to 52-week low (within 15%)
        # 2. Recommendation is 'buy' or 'strong_buy'
        # 3. Target price shows good upside
        
        is_near_low = current_price <= (low_52week * 1.15)
        is_buy = recommendation in ['buy', 'strong_buy']
        upside = (target_price - current_price) / current_price
        
        if is_near_low and is_buy and upside > 0.20:
            return {
                'Ticker': ticker,
                'Name': info.get('shortName', ticker),
                'Sector': info.get('sector', 'N/A'),
                'Price': current_price,
                '52W Low': low_52week,
                'Premium to Low': f"{((current_price / low_52week) - 1) * 100:.1f}%",
                'Target Price': target_price,
                'Upside': f"{upside * 100:.1f}%",
                'Recommendation': recommendation
            }
    except Exception:
        pass
    return None

def main():
    print("Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers. Analyzing...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(analyze_ticker, ticker): ticker for ticker in tickers}
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    # Sort by upside potential
    results.sort(key=lambda x: float(x['Upside'].strip('%')), reverse=True)
    
    df = pd.DataFrame(results)
    print("\n--- RESULTS ---")
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("No stocks found matching criteria.")
        
    df.to_csv('screener_results.csv', index=False)
    print("\nSaved to screener_results.csv")

if __name__ == "__main__":
    main()
