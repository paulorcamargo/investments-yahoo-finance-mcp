"""
Canadian Penny Stock Screener: TSX and TSX-V stocks under $10
"""
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

# Canadian small-cap / penny stocks across sectors
TICKERS = [
    # Mining / Resources
    "LUN.TO", "CS.TO", "TRQ.TO", "LUC.TO", "EDR.TO", "MAG.TO",
    "DML.TO", "NXE.TO", "CCO.TO", "FCU.TO", "FIND.TO", "EFR.TO",
    "FOM.TO", "GLO.TO", "URC.TO", "ISO.TO", "SYH.TO",
    # Cannabis
    "TLRY.TO", "WEED.TO", "ACB.TO", "OGI.TO", "CRON.TO", "HEXO.TO",
    # Tech
    "LSPD.TO", "DCBO.TO", "KXS.TO", "TIXT.TO", "TOI.TO", "CDAY.TO",
    "GURU.TO", "REAL.TO", "EGLX.TO", "MDA.TO", "BB.TO",
    # Clean Energy / EV
    "GPV.TO", "BLN.TO", "GDNP.TO",
    # Biotech / Health
    "MMED.TO", "NUMI.TO", "ABCL.TO",
    # Fintech
    "NVEI.TO", "THNK.TO", "PROPEL.TO",
    # Mining - Gold/Silver
    "WPM.TO", "FR.TO", "AG.TO", "SVM.TO", "PAAS.TO",
    "KRR.TO", "WGOLD.TO", "OGC.TO", "BTO.TO", "IAG.TO",
    # Lithium / Battery
    "LAC.TO", "ALB.TO", "SGML.TO",
    # Oil & Gas small
    "BIR.TO", "WCP.TO", "PEY.TO", "TVE.TO", "BNE.TO",
    # Misc small cap
    "GFL.TO", "CTS.TO", "WELL.TO", "PHO.TO",
    "DOO.TO", "NFI.TO", "FOOD.TO", "HUT.TO",
    # AI / Quantum
    "QBTS.TO", "PNG.TO", "MN.TO",
    # REITs small
    "GRT-UN.TO", "SRU-UN.TO",
    # Defense Canada
    "HPS-A.TO",
]

results = []
count = 0
total = len(TICKERS)

for ticker in TICKERS:
    count += 1
    if count % 15 == 0:
        print(f"  Scanning {count}/{total}...", flush=True)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("regularMarketPrice") or info.get("previousClose") or 0
        if price <= 0 or price > 10:
            continue

        yf_rec = info.get("recommendationKey", "N/A")
        num_analysts = info.get("numberOfAnalystOpinions", 0) or 0
        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        fwd_pe = info.get("forwardPE")
        roe = info.get("returnOnEquity")
        rev_growth = info.get("revenueGrowth")
        profit_margin = info.get("profitMargins")
        market_cap = info.get("marketCap", 0) or 0
        sector = info.get("sector", "N/A")
        name = info.get("shortName", ticker)
        high52 = info.get("fiftyTwoWeekHigh", 0)
        low52 = info.get("fiftyTwoWeekLow", 0)
        volume = info.get("averageVolume", 0) or 0
        div_yield = info.get("dividendYield")
        beta = info.get("beta")

        upside = ((target_mean / price) - 1) * 100 if target_mean and price > 0 else 0
        off_high = ((price / high52) - 1) * 100 if high52 and high52 > 0 else 0

        try:
            hist = stock.history(period="1mo")
            rsi = calc_rsi(hist['Close'], 14) if len(hist) >= 15 else 50
            if pd.isna(rsi): rsi = 50
        except:
            rsi = 50

        # Score
        score = 0
        if yf_rec == "strong_buy": score += 3
        elif yf_rec == "buy": score += 2
        if num_analysts >= 3: score += 1
        if upside > 50: score += 2
        elif upside > 25: score += 1
        if rev_growth and rev_growth > 0.15: score += 1
        if market_cap and market_cap > 200_000_000: score += 1
        if rsi <= 30: score += 1
        elif rsi <= 40: score += 0.5

        results.append({
            "ticker": ticker, "name": name[:25], "price": price,
            "rsi": round(rsi, 1), "yf_rec": yf_rec,
            "num_analysts": num_analysts,
            "target_mean": target_mean, "target_high": target_high,
            "upside": round(upside, 1), "off_high": round(off_high, 1),
            "rev_growth": rev_growth, "profit_margin": profit_margin,
            "market_cap": market_cap, "sector": sector,
            "score": round(score, 1), "volume": volume, "beta": beta,
        })
    except:
        pass

results.sort(key=lambda x: x['score'], reverse=True)

print(f"\n{'='*130}")
print(f"  TSX PENNY STOCK SCREENER: Canadian Stocks Under $10 ({len(results)} found)")
print(f"  Sorted by Score | May 1, 2026")
print(f"{'='*130}\n")

header = (
    f"  {'Sym':<10s} {'Name':<26s} {'Score':>5s} {'Price':>7s} {'RSI':>5s} "
    f"{'Rating':>11s} {'#Ana':>4s} {'Target':>8s} {'Upside':>7s} {'Off Hi':>7s} "
    f"{'RevG':>6s} {'MCap':>8s} {'Sector':>15s}"
)
print(header)
print("-" * 130)

for r in results:
    tgt = f"${r['target_mean']:.1f}" if r['target_mean'] else "   N/A"
    rev_s = f"{r['rev_growth']*100:.0f}%" if r['rev_growth'] else "  N/A"
    mcap_s = f"${r['market_cap']/1e9:.1f}B" if r['market_cap'] >= 1e9 else f"${r['market_cap']/1e6:.0f}M" if r['market_cap'] else "N/A"
    sect = (r['sector'] or 'N/A')[:15]

    flag = ""
    if r['rsi'] <= 30: flag = " OVERSOLD"
    if r['upside'] >= 100: flag += " ***"
    elif r['upside'] >= 50: flag += " **"

    print(
        f"  {r['ticker']:<10s} {r['name']:<26s} {r['score']:>5.1f} ${r['price']:>6.2f} {r['rsi']:>5.1f} "
        f"{r['yf_rec']:>11s} {r['num_analysts']:>4d} {tgt:>8s} {r['upside']:>6.1f}% {r['off_high']:>6.1f}% "
        f"{rev_s:>6s} {mcap_s:>8s} {sect:>15s}{flag}"
    )
