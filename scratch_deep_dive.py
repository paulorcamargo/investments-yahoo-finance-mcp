"""
Deep Dive: Oversold + Buy-Rated + Strong Fundamentals
Filters for: RSI <= 45, analyst Buy/Strong Buy, and quality metrics.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import yfinance as yf
import pandas as pd
import json

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

TICKERS = [
    # From previous scan - all with RSI <= 45 or interesting
    "LMT", "NOC", "RTX", "NFLX", "STZ", "MCD", "JNJ", "HD", "MRK",
    "GE", "PFE", "LOW", "DE", "MA", "BRK-B", "META", "IBM",
    # Additional quality to check
    "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "AVGO", "UNH", "PG",
    "COST", "V", "JPM", "ORCL", "ABBV", "CVX", "XOM", "CRM",
    "NKE", "DIS", "SBUX", "TGT", "PYPL", "SHOP", "UBER",
    "GD", "BA", "CAT", "CSCO", "INTC", "AMD", "KO", "PEP", "WMT",
    "ADBE", "NOW", "ISRG", "PANW", "T", "VZ", "O",
    # Canadian
    "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "ENB.TO", "CNQ.TO", "BCE.TO",
    # ETFs with fundamentals
    "ITA", "QQQ", "SMH",
]

results = []
count = 0
total = len(TICKERS)

for ticker in TICKERS:
    count += 1
    if count % 10 == 0:
        print(f"  Analyzing {count}/{total}...", flush=True)
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if len(hist) < 15:
            continue
        rsi = calc_rsi(hist['Close'], 14)
        if pd.isna(rsi):
            continue

        info = stock.info
        price = info.get("regularMarketPrice") or info.get("previousClose") or 0
        if price <= 0:
            continue

        yf_rec = info.get("recommendationKey", "N/A")
        num_analysts = info.get("numberOfAnalystOpinions", 0) or 0
        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        target_low = info.get("targetLowPrice")
        fwd_pe = info.get("forwardPE")
        trail_pe = info.get("trailingPE")
        peg = info.get("pegRatio")
        roe = info.get("returnOnEquity")
        rev_growth = info.get("revenueGrowth")
        earn_growth = info.get("earningsGrowth")
        profit_margin = info.get("profitMargins")
        op_margin = info.get("operatingMargins")
        div_yield = info.get("dividendYield")
        beta = info.get("beta")
        de_ratio = info.get("debtToEquity")
        fcf = info.get("freeCashflow")
        market_cap = info.get("marketCap", 0)
        sector = info.get("sector", "ETF")
        name = info.get("shortName", ticker)
        high52 = info.get("fiftyTwoWeekHigh", 0)
        low52 = info.get("fiftyTwoWeekLow", 0)
        current_ratio = info.get("currentRatio")

        upside = ((target_mean / price) - 1) * 100 if target_mean and price > 0 else 0
        off_high = ((price / high52) - 1) * 100 if high52 and high52 > 0 else 0
        above_low = ((price / low52) - 1) * 100 if low52 and low52 > 0 else 0

        # Quality score (0-10)
        score = 0
        # Analyst rating
        if yf_rec == "strong_buy": score += 2
        elif yf_rec == "buy": score += 1.5
        # Upside to target
        if upside and upside > 20: score += 2
        elif upside and upside > 10: score += 1
        # RSI oversold
        if rsi <= 30: score += 2
        elif rsi <= 40: score += 1
        elif rsi <= 45: score += 0.5
        # Profitability
        if profit_margin and profit_margin > 0.20: score += 1
        elif profit_margin and profit_margin > 0.10: score += 0.5
        # Growth
        if rev_growth and rev_growth > 0.10: score += 1
        elif rev_growth and rev_growth > 0.05: score += 0.5
        # ROE
        if roe and roe > 0.20: score += 1
        elif roe and roe > 0.10: score += 0.5

        results.append({
            "ticker": ticker, "name": name[:22], "price": price,
            "rsi": round(rsi, 1), "yf_rec": yf_rec,
            "num_analysts": num_analysts,
            "target_mean": target_mean, "target_high": target_high, "target_low": target_low,
            "upside": round(upside, 1), "off_high": round(off_high, 1),
            "fwd_pe": fwd_pe, "trail_pe": trail_pe, "peg": peg,
            "roe": roe, "rev_growth": rev_growth, "earn_growth": earn_growth,
            "profit_margin": profit_margin, "op_margin": op_margin,
            "div_yield": div_yield, "beta": beta, "de_ratio": de_ratio,
            "sector": sector, "market_cap": market_cap,
            "score": round(score, 1), "above_low": round(above_low, 1),
        })
    except:
        pass

# Filter: only Buy/Strong Buy with good score
buy_rated = [r for r in results if r['yf_rec'] in ('buy', 'strong_buy') and r['score'] >= 4]
buy_rated.sort(key=lambda x: x['score'], reverse=True)

print(f"\n{'='*130}")
print(f"  TOP PICKS: Buy/Strong Buy + Strong Fundamentals + Oversold/Near-Oversold")
print(f"  {len(buy_rated)} stocks passed filters (from {len(results)} analyzed)")
print(f"{'='*130}\n")

header = (
    f"  {'Sym':<8s} {'Name':<23s} {'Score':>5s} {'RSI':>5s} "
    f"{'Rating':>11s} {'#Ana':>4s} {'Price':>8s} {'Target':>8s} {'Upside':>7s} "
    f"{'FwdPE':>6s} {'ROE':>6s} {'RevG':>6s} {'Margin':>7s} {'Div%':>5s} {'Sector':>15s}"
)
print(header)
print("-" * 130)

for r in buy_rated:
    fpe = f"{r['fwd_pe']:.1f}" if r['fwd_pe'] else "  N/A"
    roe_s = f"{r['roe']*100:.0f}%" if r['roe'] else " N/A"
    rev_s = f"{r['rev_growth']*100:.0f}%" if r['rev_growth'] else " N/A"
    mar_s = f"{r['profit_margin']*100:.0f}%" if r['profit_margin'] else "  N/A"
    dy = f"{r['div_yield']*100:.1f}%" if r['div_yield'] else " N/A"
    tgt = f"${r['target_mean']:.0f}" if r['target_mean'] else "   N/A"
    sect = (r['sector'] or 'N/A')[:15]

    flag = ""
    if r['rsi'] <= 30: flag = " <<< OVERSOLD"
    elif r['rsi'] <= 40: flag = " << NEAR"

    print(
        f"  {r['ticker']:<8s} {r['name']:<23s} {r['score']:>5.1f} {r['rsi']:>5.1f} "
        f"{r['yf_rec']:>11s} {r['num_analysts']:>4d} ${r['price']:>7.2f} {tgt:>8s} {r['upside']:>6.1f}% "
        f"{fpe:>6s} {roe_s:>6s} {rev_s:>6s} {mar_s:>7s} {dy:>5s} {sect:>15s}{flag}"
    )

# Deep dive on top 10
print(f"\n\n{'='*130}")
print("  DEEP DIVE — Top 10 Candidates")
print(f"{'='*130}")

for i, r in enumerate(buy_rated[:10], 1):
    tgt_lo = f"${r['target_low']:.0f}" if r['target_low'] else "N/A"
    tgt_hi = f"${r['target_high']:.0f}" if r['target_high'] else "N/A"
    tgt_mean = f"${r['target_mean']:.0f}" if r['target_mean'] else "N/A"
    roe_s = f"{r['roe']*100:.1f}%" if r['roe'] else "N/A"
    rev_s = f"{r['rev_growth']*100:.1f}%" if r['rev_growth'] else "N/A"
    earn_s = f"{r['earn_growth']*100:.1f}%" if r['earn_growth'] else "N/A"
    mar_s = f"{r['profit_margin']*100:.1f}%" if r['profit_margin'] else "N/A"
    op_s = f"{r['op_margin']*100:.1f}%" if r['op_margin'] else "N/A"
    dy = f"{r['div_yield']*100:.2f}%" if r['div_yield'] else "N/A"
    peg_s = f"{r['peg']:.2f}" if r['peg'] else "N/A"
    de_s = f"{r['de_ratio']:.0f}" if r['de_ratio'] else "N/A"
    mcap = f"${r['market_cap']/1e9:.0f}B" if r['market_cap'] else "N/A"

    print(f"\n  #{i}. {r['ticker']} — {r['name']}  [Score: {r['score']}/10]")
    print(f"      Price: ${r['price']:.2f} | RSI: {r['rsi']} | Rating: {r['yf_rec']} ({r['num_analysts']} analysts)")
    print(f"      Target: {tgt_mean} (Low: {tgt_lo}, High: {tgt_hi}) | Upside: {r['upside']}%")
    print(f"      Fwd P/E: {r['fwd_pe'] or 'N/A'} | PEG: {peg_s} | Market Cap: {mcap}")
    print(f"      ROE: {roe_s} | Rev Growth: {rev_s} | Earnings Growth: {earn_s}")
    print(f"      Profit Margin: {mar_s} | Op Margin: {op_s}")
    print(f"      Dividend: {dy} | Beta: {r['beta']} | D/E: {de_s}")
    print(f"      Off 52W High: {r['off_high']}% | Above 52W Low: {r['above_low']}%")

# Save for artifact
with open('scratch_deep_dive.json', 'w') as f:
    json.dump(buy_rated[:15], f, indent=2, default=str)
