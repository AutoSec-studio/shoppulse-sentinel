#!/usr/bin/env python3
"""
ShopPulse Sentinel Lite - Free & Open-Core E-Commerce Checkout Healthcheck.
Lightweight watchdog that monitors your checkout endpoint and pings Telegram if it fails.

Upgrade to ShopPulse Sentinel PRO ($10 Lifetime) for:
- Silent 200 OK Content Assertions
- Catalog Stockout & Price Drop Anomaly Protection
- WhatsApp, Slack & SMTP Email Channels
- Docker Compose, Cooldown Filters & Outgoing Webhooks (n8n / Make)
Whop: https://whop.com/autosec/autosec-e-commerce-revenue-leak-detection/
Payhip: https://payhip.com/b/fZx6v
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECKOUT_URL = os.getenv("CHECKOUT_URL", "https://httpbin.org/status/200")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "10"))


def send_telegram_alert(message: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("  ⚠️ [ALERT TRIGGERED] Telegram bot not configured. Alert logged to console.")
        print(f"  {message}")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=8)
        if resp.status_code == 200 and resp.json().get("ok"):
            print("  ✅ Telegram alert dispatched successfully.")
        else:
            print(f"  ❌ Telegram API error: {resp.text}")
    except Exception as exc:
        print(f"  ❌ Failed to send Telegram alert: {exc}")


def check_endpoint() -> bool:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] Checking endpoint: {CHECKOUT_URL}...")
    try:
        start = time.time()
        resp = requests.get(CHECKOUT_URL, timeout=TIMEOUT_SECONDS, headers={"User-Agent": "ShopPulseSentinel-Lite/1.0"})
        latency_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            print(f"  🟢 Healthy: 200 OK ({latency_ms}ms)")
            return True
        else:
            print(f"  🚨 Error: HTTP {resp.status_code} ({latency_ms}ms)")
            send_telegram_alert(
                f"🚨 <b>[CRITICAL] Checkout Failure Detected</b>\n\n"
                f"• <b>URL:</b> {CHECKOUT_URL}\n"
                f"• <b>Status:</b> HTTP {resp.status_code} (Expected 200)\n"
                f"• <b>Latency:</b> {latency_ms}ms\n"
                f"• <b>Time:</b> {timestamp}\n\n"
                f"⚠️ <i>Please inspect your store payment gateway immediately.</i>"
            )
            return False
    except requests.exceptions.RequestException as exc:
        print(f"  🚨 Connection Exception: {exc}")
        send_telegram_alert(
            f"🚨 <b>[CRITICAL] Checkout Connection Timeout / Crash</b>\n\n"
            f"• <b>URL:</b> {CHECKOUT_URL}\n"
            f"• <b>Error:</b> {str(exc)[:200]}\n"
            f"• <b>Time:</b> {timestamp}"
        )
        return False


def main() -> None:
    print("=" * 65)
    print("🛒  ShopPulse Sentinel LITE v1.0.0 (Open-Core)")
    print("    Free E-Commerce Checkout Healthcheck & Telegram Watchdog")
    print("=" * 65)
    print(f"• Target URL: {CHECKOUT_URL}")
    print(f"• Interval:   Every {CHECK_INTERVAL_SECONDS} seconds")
    print(f"• Channel:    Telegram Bot ({'Configured' if BOT_TOKEN else 'Console Mode'})")
    print("=" * 65)
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            check_endpoint()
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nShutting down Sentinel Lite. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
