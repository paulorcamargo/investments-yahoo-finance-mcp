"""
Stock Signal Monitor — Watches your portfolio for BUY signal changes.

Checks TradingView technical signals and Yahoo Finance consensus recommendations
at a configurable interval. Sends Windows desktop notifications when a holding
transitions to BUY or STRONG_BUY.

Usage:
    py stock_monitor.py                  # Run once (good for Task Scheduler)
    py stock_monitor.py --loop           # Run continuously every 30 minutes
    py stock_monitor.py --loop --interval 15   # Check every 15 minutes
    py stock_monitor.py --email          # Also send email alerts

Tip:  To run this automatically, create a Windows Task Scheduler job:
      Action: py  |  Arguments: stock_monitor.py  |  Trigger: Every 30 min
"""

import argparse
import os
import json
import logging
import smtplib
import time
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from tradingview_ta import TA_Handler, Interval
import yfinance as yf

# ---------------------------------------------------------------------------
# Configuration — EDIT THESE
# ---------------------------------------------------------------------------

# Your portfolio tickers mapped to (exchange, screener) for TradingView
WATCHLIST = {
    # --- Current Portfolio ---
    "META":  ("NASDAQ", "america"),
    "MSFT":  ("NASDAQ", "america"),
    "ORCL":  ("NYSE",   "america"),
    "SIRI":  ("NASDAQ", "america"),
    "STZ":   ("NYSE",   "america"),
    "KULR":  ("AMEX",   "america"),
    "QQQ":   ("NASDAQ", "america"),
    "RY":    ("TSX",    "canada"),
    "FSZ":   ("TSX",    "canada"),
    "VCN":   ("TSX",    "canada"),
    "XAW":   ("TSX",    "canada"),
    "ZEA":   ("TSX",    "canada"),
    "XIT":   ("TSX",    "canada"),
    # --- Defense & Aerospace ---
    "LMT":   ("NYSE",   "america"),
    "RTX":   ("NYSE",   "america"),
    "GD":    ("NYSE",   "america"),
    "NOC":   ("NYSE",   "america"),
    "ITA":   ("AMEX",   "america"),
    "PPA":   ("NASDAQ", "america"),
    "XAR":   ("AMEX",   "america"),
    # --- India (China+1 Diversification) ---
    "INDA":  ("NASDAQ", "america"),
    "INDY":  ("NASDAQ", "america"),
    "EPI":   ("AMEX",   "america"),
    # --- Mexico Nearshoring ---
    "EWW":   ("AMEX",   "america"),
    # --- Low-MER Canadian ETFs ---
    "XEQT":  ("TSX",    "canada"),
    "VEQT":  ("TSX",    "canada"),
    "VFV":   ("TSX",    "canada"),
    "ZSP":   ("TSX",    "canada"),
    "HXS":   ("TSX",    "canada"),
    "XGRO":  ("TSX",    "canada"),
    "VGRO":  ("TSX",    "canada"),
    # --- Quality Stocks ---
    "JNJ":   ("NYSE",   "america"),
    "PG":    ("NYSE",   "america"),
    "UNH":   ("NYSE",   "america"),
    "COST":  ("NASDAQ", "america"),
    "BRK.B": ("NYSE",   "america"),
    "AMZN":  ("NASDAQ", "america"),
    "GOOGL": ("NASDAQ", "america"),
    "AVGO":  ("NASDAQ", "america"),
    # --- Oversold Quality (Screener Picks) ---
    "NFLX":  ("NASDAQ", "america"),
    "GE":    ("NYSE",   "america"),
    "MA":    ("NASDAQ", "america"),
    "MCD":   ("NYSE",   "america"),
    "HD":    ("NYSE",   "america"),
    "LOW":   ("NYSE",   "america"),
    "MRK":   ("NYSE",   "america"),
    "PFE":   ("NYSE",   "america"),
    "CRM":   ("NYSE",   "america"),
    "NKE":   ("NYSE",   "america"),
    "DIS":   ("NYSE",   "america"),
    # --- US Penny Stocks (High Risk) ---
    "SOUN":  ("NASDAQ", "america"),
    "GENI":  ("NYSE",   "america"),
    "RDW":   ("NYSE",   "america"),
    "QUBT":  ("NASDAQ", "america"),
    "GRAB":  ("NASDAQ", "america"),
    "SENS":  ("AMEX",   "america"),
    "NTLA":  ("NASDAQ", "america"),
    "ACHR":  ("NYSE",   "america"),
    "NXE":   ("NYSE",   "america"),
    "LCID":  ("NASDAQ", "america"),
    "TLRY":  ("NASDAQ", "america"),
    "AISP":  ("NASDAQ", "america"),
    # --- TSX Penny Stocks (High Risk) ---
    "OGI":   ("TSX",    "canada"),
    "BTO":   ("TSX",    "canada"),
    "URC":   ("TSX",    "canada"),
    "WELL":  ("TSX",    "canada"),
    "DML":   ("TSX",    "canada"),
    "BIR":   ("TSX",    "canada"),
    "GURU":  ("TSX",    "canada"),
    "REAL":  ("TSX",    "canada"),
    # --- Watching for Pullback ---
    "NOK":   ("NYSE",   "america"),
}

# Yahoo Finance tickers (some Canadian tickers need .TO suffix)
YF_TICKERS = {
    # Current Portfolio
    "META": "META", "MSFT": "MSFT", "ORCL": "ORCL", "SIRI": "SIRI",
    "STZ": "STZ", "KULR": "KULR", "QQQ": "QQQ",
    "RY": "RY.TO", "FSZ": "FSZ.TO", "VCN": "VCN.TO",
    "XAW": "XAW.TO", "ZEA": "ZEA.TO", "XIT": "XIT.TO",
    # Defense & Aerospace
    "LMT": "LMT", "RTX": "RTX", "GD": "GD", "NOC": "NOC",
    "ITA": "ITA", "PPA": "PPA", "XAR": "XAR",
    # India
    "INDA": "INDA", "INDY": "INDY", "EPI": "EPI",
    # Mexico
    "EWW": "EWW",
    # Low-MER Canadian ETFs
    "XEQT": "XEQT.TO", "VEQT": "VEQT.TO", "VFV": "VFV.TO",
    "ZSP": "ZSP.TO", "HXS": "HXS.TO", "XGRO": "XGRO.TO", "VGRO": "VGRO.TO",
    # Quality Stocks
    "JNJ": "JNJ", "PG": "PG", "UNH": "UNH", "COST": "COST",
    "BRK.B": "BRK-B", "AMZN": "AMZN", "GOOGL": "GOOGL", "AVGO": "AVGO",
    # Oversold Quality
    "NFLX": "NFLX", "GE": "GE", "MA": "MA", "MCD": "MCD",
    "HD": "HD", "LOW": "LOW", "MRK": "MRK", "PFE": "PFE",
    "CRM": "CRM", "NKE": "NKE", "DIS": "DIS",
    # US Penny Stocks
    "SOUN": "SOUN", "GENI": "GENI", "RDW": "RDW", "QUBT": "QUBT",
    "GRAB": "GRAB", "SENS": "SENS", "NTLA": "NTLA", "ACHR": "ACHR",
    "NXE": "NXE", "LCID": "LCID", "TLRY": "TLRY", "AISP": "AISP",
    # TSX Penny Stocks
    "OGI": "OGI.TO", "BTO": "BTO.TO", "URC": "URC.TO", "WELL": "WELL.TO",
    "DML": "DML.TO", "BIR": "BIR.TO", "GURU": "GURU.TO", "REAL": "REAL.TO",
    # Watching for Pullback
    "NOK": "NOK",
}

# Signals we consider "buy" triggers
BUY_SIGNALS_TV = {"BUY", "STRONG_BUY"}
BUY_SIGNALS_YF = {"buy", "strong_buy"}

# Email settings (optional — fill in to enable email alerts)
EMAIL_CONFIG = {
    "enabled": True,                        # Email alerts active
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": os.environ.get("STOCK_MONITOR_EMAIL", "paulorobertodecamargofilho@gmail.com"),
    "sender_password": os.environ.get("STOCK_MONITOR_PASSWORD", ""),  # Set env var STOCK_MONITOR_PASSWORD
    "recipient_email": "paulocamargo@hotmail.com",
}

# State file — tracks previous signals to detect changes
STATE_FILE = Path(__file__).parent / "monitor_state.json"
LOG_FILE = Path(__file__).parent / "monitor_log.txt"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ]
)
logger = logging.getLogger("stock_monitor")

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def get_tv_signal(symbol: str, exchange: str, screener: str) -> dict:
    """Get TradingView daily recommendation for a symbol."""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY,
        )
        analysis = handler.get_analysis()
        return {
            "tv_recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
            "tv_buy_count": analysis.summary.get("BUY", 0),
            "tv_sell_count": analysis.summary.get("SELL", 0),
            "tv_rsi": round(analysis.indicators.get("RSI", 0) or 0, 2),
            "tv_close": round(analysis.indicators.get("close", 0) or 0, 2),
        }
    except Exception as e:
        logger.debug("TradingView error for %s: %s", symbol, e)
        return {"tv_recommendation": "ERROR", "tv_error": str(e)}


def get_yf_signal(symbol: str, yf_ticker: str) -> dict:
    """Get Yahoo Finance consensus recommendation for a symbol."""
    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        return {
            "yf_recommendation": info.get("recommendationKey", "none"),
            "yf_target": info.get("targetMeanPrice"),
            "yf_price": info.get("currentPrice", info.get("regularMarketPrice")),
        }
    except Exception as e:
        logger.debug("Yahoo Finance error for %s: %s", symbol, e)
        return {"yf_recommendation": "error", "yf_error": str(e)}

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def send_desktop_notification(title: str, message: str):
    """Send a Windows desktop toast notification."""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Stock Monitor",
            timeout=15,
        )
        logger.info("Desktop notification sent: %s", title)
    except Exception as e:
        logger.warning("Desktop notification failed: %s", e)


def send_email_notification(subject: str, body: str):
    """Send an email alert (if configured)."""
    if not EMAIL_CONFIG["enabled"]:
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = EMAIL_CONFIG["recipient_email"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)

        logger.info("Email sent: %s", subject)
    except Exception as e:
        logger.warning("Email notification failed: %s", e)

# ---------------------------------------------------------------------------
# Core monitoring logic
# ---------------------------------------------------------------------------

def check_signals() -> list[dict]:
    """
    Check all watchlist tickers. Returns a list of signal changes
    where a ticker has transitioned TO a buy signal.
    """
    previous_state = load_state()
    current_state = {}
    changes = []
    now = datetime.datetime.now().isoformat(timespec="seconds")

    for symbol, (exchange, screener) in WATCHLIST.items():
        logger.info("Checking %s ...", symbol)

        # Fetch signals
        tv = get_tv_signal(symbol, exchange, screener)
        yf_ticker = YF_TICKERS.get(symbol, symbol)
        yf_data = get_yf_signal(symbol, yf_ticker)

        # Combine
        current = {**tv, **yf_data, "checked_at": now}
        current_state[symbol] = current

        # Compare with previous state
        prev = previous_state.get(symbol, {})
        prev_tv = prev.get("tv_recommendation", "UNKNOWN")
        prev_yf = prev.get("yf_recommendation", "unknown")
        curr_tv = current.get("tv_recommendation", "N/A")
        curr_yf = current.get("yf_recommendation", "none")

        # Detect transitions TO buy
        tv_became_buy = (curr_tv in BUY_SIGNALS_TV and prev_tv not in BUY_SIGNALS_TV)
        yf_became_buy = (curr_yf in BUY_SIGNALS_YF and prev_yf not in BUY_SIGNALS_YF)

        # Also detect when BOTH sources agree on buy (consensus buy)
        both_buy = (curr_tv in BUY_SIGNALS_TV and curr_yf in BUY_SIGNALS_YF)
        prev_both = (prev_tv in BUY_SIGNALS_TV and prev_yf in BUY_SIGNALS_YF)
        consensus_new = both_buy and not prev_both

        if tv_became_buy or yf_became_buy or consensus_new:
            change = {
                "symbol": symbol,
                "type": [],
                "tv_prev": prev_tv,
                "tv_now": curr_tv,
                "yf_prev": prev_yf,
                "yf_now": curr_yf,
                "price": current.get("tv_close") or current.get("yf_price"),
                "target": current.get("yf_target"),
                "rsi": current.get("tv_rsi"),
            }
            if tv_became_buy:
                change["type"].append("TradingView → BUY")
            if yf_became_buy:
                change["type"].append("Yahoo Finance → BUY")
            if consensus_new:
                change["type"].append("⭐ CONSENSUS BUY (both sources)")
            changes.append(change)

    # Save new state
    save_state(current_state)
    return changes


def notify_changes(changes: list[dict], send_email: bool = False):
    """Send notifications for all detected signal changes."""
    if not changes:
        logger.info("No new buy signals detected.")
        return

    for ch in changes:
        symbol = ch["symbol"]
        signals = " + ".join(ch["type"])
        price = ch.get("price", "?")
        target = ch.get("target")
        rsi = ch.get("rsi")

        title = f"🟢 BUY Signal: {symbol}"
        lines = [
            f"Signal: {signals}",
            f"Price: ${price}",
        ]
        if target:
            upside = round(((target / price) - 1) * 100, 1) if price and price > 0 else 0
            lines.append(f"Target: ${target} ({upside}% upside)")
        if rsi:
            lines.append(f"RSI: {rsi}")
        lines.append(f"TV: {ch['tv_prev']} → {ch['tv_now']}")
        lines.append(f"YF: {ch['yf_prev']} → {ch['yf_now']}")

        message = "\n".join(lines)

        logger.info("=== SIGNAL CHANGE: %s ===\n%s", symbol, message)
        send_desktop_notification(title, message)

        if send_email:
            send_email_notification(
                f"Stock Alert: {symbol} — New BUY Signal",
                f"Stock Monitor Alert\n{'='*40}\n\n{symbol}\n\n{message}\n\n"
                f"Checked at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

    # Summary notification if multiple changes
    if len(changes) > 1:
        symbols = ", ".join(ch["symbol"] for ch in changes)
        send_desktop_notification(
            f"📊 {len(changes)} New Buy Signals",
            f"Stocks: {symbols}\nCheck monitor_log.txt for details."
        )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stock Signal Monitor")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in minutes (default: 30)")
    parser.add_argument("--email", action="store_true", help="Also send email alerts")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Stock Monitor started — watching %d tickers", len(WATCHLIST))
    logger.info("=" * 60)

    if args.loop:
        logger.info("Running in loop mode. Checking every %d minutes.", args.interval)
        logger.info("Press Ctrl+C to stop.\n")
        while True:
            try:
                changes = check_signals()
                notify_changes(changes, send_email=args.email)
                logger.info("Next check in %d minutes...\n", args.interval)
                time.sleep(args.interval * 60)
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user.")
                break
            except Exception as e:
                logger.error("Error during check: %s", e, exc_info=True)
                time.sleep(60)  # Wait 1 min on error, then retry
    else:
        # Single run
        changes = check_signals()
        notify_changes(changes, send_email=args.email)
        logger.info("Single check complete.")


if __name__ == "__main__":
    main()
