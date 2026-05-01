"""Quick deep-dive analysis on Nokia (NOK)."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import yfinance as yf
import pandas as pd

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50

stock = yf.Ticker("NOK")
info = stock.info
hist = stock.history(period="1mo")
rsi = calc_rsi(hist['Close'], 14) if len(hist) >= 15 else 50

price = info.get("regularMarketPrice") or info.get("previousClose") or 0
target = info.get("targetMeanPrice")
target_high = info.get("targetHighPrice")
target_low = info.get("targetLowPrice")
upside = ((target / price) - 1) * 100 if target and price > 0 else 0

print("=" * 65)
print(f"  NOKIA (NOK) — Deep Dive Analysis")
print(f"  {info.get('longName', 'Nokia Oyj')}")
print("=" * 65)

print(f"\n  PRICE & TECHNICALS")
print(f"  {'Price:':<25s} ${price:.2f}")
print(f"  {'52W High:':<25s} ${info.get('fiftyTwoWeekHigh', 0):.2f}")
print(f"  {'52W Low:':<25s} ${info.get('fiftyTwoWeekLow', 0):.2f}")
off_high = ((price / info.get('fiftyTwoWeekHigh', 1)) - 1) * 100
print(f"  {'Off 52W High:':<25s} {off_high:.1f}%")
print(f"  {'RSI(14):':<25s} {rsi:.1f}")
print(f"  {'Beta:':<25s} {info.get('beta', 'N/A')}")

print(f"\n  ANALYST CONSENSUS")
print(f"  {'Recommendation:':<25s} {info.get('recommendationKey', 'N/A')}")
print(f"  {'# of Analysts:':<25s} {info.get('numberOfAnalystOpinions', 'N/A')}")
print(f"  {'Target (Mean):':<25s} ${target:.2f}" if target else "  Target: N/A")
print(f"  {'Target (Low):':<25s} ${target_low:.2f}" if target_low else "")
print(f"  {'Target (High):':<25s} ${target_high:.2f}" if target_high else "")
print(f"  {'Upside to Target:':<25s} {upside:.1f}%")

print(f"\n  VALUATION")
print(f"  {'Forward P/E:':<25s} {info.get('forwardPE', 'N/A')}")
print(f"  {'Trailing P/E:':<25s} {info.get('trailingPE', 'N/A')}")
print(f"  {'PEG Ratio:':<25s} {info.get('pegRatio', 'N/A')}")
print(f"  {'Price/Book:':<25s} {info.get('priceToBook', 'N/A')}")
print(f"  {'EV/EBITDA:':<25s} {info.get('enterpriseToEbitda', 'N/A')}")
mcap = info.get('marketCap', 0)
print(f"  {'Market Cap:':<25s} ${mcap/1e9:.1f}B" if mcap else "  Market Cap: N/A")

print(f"\n  PROFITABILITY")
roe = info.get('returnOnEquity')
print(f"  {'ROE:':<25s} {roe*100:.1f}%" if roe else f"  {'ROE:':<25s} N/A")
pm = info.get('profitMargins')
print(f"  {'Profit Margin:':<25s} {pm*100:.1f}%" if pm else f"  {'Profit Margin:':<25s} N/A")
om = info.get('operatingMargins')
print(f"  {'Operating Margin:':<25s} {om*100:.1f}%" if om else f"  {'Operating Margin:':<25s} N/A")
gm = info.get('grossMargins')
print(f"  {'Gross Margin:':<25s} {gm*100:.1f}%" if gm else f"  {'Gross Margin:':<25s} N/A")

print(f"\n  GROWTH")
rg = info.get('revenueGrowth')
print(f"  {'Revenue Growth:':<25s} {rg*100:.1f}%" if rg else f"  {'Revenue Growth:':<25s} N/A")
eg = info.get('earningsGrowth')
print(f"  {'Earnings Growth:':<25s} {eg*100:.1f}%" if eg else f"  {'Earnings Growth:':<25s} N/A")

print(f"\n  BALANCE SHEET")
de = info.get('debtToEquity')
print(f"  {'Debt/Equity:':<25s} {de:.1f}" if de else f"  {'Debt/Equity:':<25s} N/A")
cr = info.get('currentRatio')
print(f"  {'Current Ratio:':<25s} {cr:.2f}" if cr else f"  {'Current Ratio:':<25s} N/A")
fcf = info.get('freeCashflow')
print(f"  {'Free Cash Flow:':<25s} ${fcf/1e9:.2f}B" if fcf else f"  {'Free Cash Flow:':<25s} N/A")
cash = info.get('totalCash')
print(f"  {'Total Cash:':<25s} ${cash/1e9:.2f}B" if cash else f"  {'Total Cash:':<25s} N/A")
debt = info.get('totalDebt')
print(f"  {'Total Debt:':<25s} ${debt/1e9:.2f}B" if debt else f"  {'Total Debt:':<25s} N/A")

print(f"\n  DIVIDENDS")
dy = info.get('dividendYield')
print(f"  {'Dividend Yield:':<25s} {dy*100:.2f}%" if dy else f"  {'Dividend Yield:':<25s} N/A")
pr = info.get('payoutRatio')
print(f"  {'Payout Ratio:':<25s} {pr*100:.1f}%" if pr else f"  {'Payout Ratio:':<25s} N/A")

print(f"\n  SECTOR & INDUSTRY")
print(f"  {'Sector:':<25s} {info.get('sector', 'N/A')}")
print(f"  {'Industry:':<25s} {info.get('industry', 'N/A')}")

# TradingView
try:
    from tradingview_ta import TA_Handler, Interval
    import time
    time.sleep(2)
    h = TA_Handler(symbol="NOK", screener="america", exchange="NYSE", interval=Interval.INTERVAL_1_DAY)
    a = h.get_analysis()
    tv_rec = a.summary.get("RECOMMENDATION", "N/A")
    tv_buy = a.summary.get("BUY", 0)
    tv_sell = a.summary.get("SELL", 0)
    tv_neutral = a.summary.get("NEUTRAL", 0)
    stoch = a.indicators.get("Stoch.K", 0) or 0
    macd = a.indicators.get("MACD.macd", 0) or 0
    macd_sig = a.indicators.get("MACD.signal", 0) or 0
    print(f"\n  TRADINGVIEW SIGNALS")
    print(f"  {'Signal:':<25s} {tv_rec}")
    print(f"  {'Buy/Neutral/Sell:':<25s} {tv_buy} / {tv_neutral} / {tv_sell}")
    print(f"  {'Stochastic K:':<25s} {stoch:.1f}")
    print(f"  {'MACD:':<25s} {macd:.4f} (Signal: {macd_sig:.4f})")
    macd_dir = "BULLISH" if macd > macd_sig else "BEARISH"
    print(f"  {'MACD Direction:':<25s} {macd_dir}")
except Exception as e:
    print(f"\n  TradingView: Unavailable ({e})")
