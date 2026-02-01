import os
import time
import math
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")

SYMBOL = os.getenv("SYMBOL", "ASTS")
THRESHOLD_USD = float(os.getenv("THRESHOLD_USD", "1.0"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
MIN_ALERT_GAP_SECONDS = int(os.getenv("MIN_ALERT_GAP_SECONDS", "20"))

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not FINNHUB_TOKEN:
    raise SystemExit("Chybí env proměnné: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FINNHUB_TOKEN (v .env)")

def get_price(symbol: str) -> float:
    url = "https://finnhub.io/api/v1/quote"
    r = requests.get(url, params={"symbol": symbol, "token": FINNHUB_TOKEN}, timeout=10)
    r.raise_for_status()
    data = r.json()
    price = data.get("c")
    if price is None or price == 0:
        raise RuntimeError(f"Neplatná cena z API: {data}")
    return float(price)

def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()

def main():
    last_alert_price = get_price(SYMBOL)
    last_alert_ts = 0

    send_telegram(
        f"✅ Start: sleduju {SYMBOL}. Cena: ${last_alert_price:.2f}. "
        f"Alert po změně ±${THRESHOLD_USD:.2f}."
    )

    while True:
        try:
            price = get_price(SYMBOL)
            diff = price - last_alert_price
            now = time.time()

            # proti spamování (minimální čas mezi alerty)
            if now - last_alert_ts < MIN_ALERT_GAP_SECONDS:
                time.sleep(POLL_SECONDS)
                continue

            if abs(diff) >= THRESHOLD_USD:
                steps = math.floor(abs(diff) / THRESHOLD_USD)
                direction = "📈" if diff > 0 else "📉"
                sign = "+" if diff > 0 else "-"

                send_telegram(
                    f"{SYMBOL.lower()} at ${price:.2f} is crazy"
                )


                # posun “po schodech” o celé kroky 1 USD
                last_alert_price = last_alert_price + (THRESHOLD_USD * steps * (1 if diff > 0 else -1))
                last_alert_ts = now

        except Exception as e:
            print("ERROR:", e)

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()

