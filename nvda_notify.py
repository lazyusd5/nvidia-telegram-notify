import yfinance as yf
import requests
import datetime
import pytz
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def get_price():
    ticker = yf.Ticker("NVDA")
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        return None
    return data["Close"].iloc[-1]

def main():
    bangkok = pytz.timezone("Asia/Bangkok")
    now = datetime.datetime.now(bangkok).strftime("%Y-%m-%d %H:%M:%S")

    price = get_price()
    if price is None:
        send_telegram(f"❗ Error: ไม่พบข้อมูลราคาหุ้น NVDA ({now})")
        return

    msg = (
        "🔔 *NVDA Price Alert (Test Mode)*\n\n"
        f"⏰ เวลาไทย: {now}\n"
        f"💵 ราคา: {price:.2f} USD\n"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()
