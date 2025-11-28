import os
import yfinance as yf
import requests
from datetime import datetime
import pytz

# ------------------------- CONFIG -------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ใส่ chat id ของคุณ
SYMBOL = "NVDA"
INTERVAL = "5m"
TIMEZONE = "US/Eastern"

# ------------------------- FUNCTIONS -------------------------
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Telegram send failed: {e}")

def is_market_open():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    # NYSE ตลาดเปิด Mon-Fri 9:30-16:00
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now <= close_time

def fetch_data():
    ticker = yf.Ticker(SYMBOL)
    data_5m = ticker.history(period="1d", interval=INTERVAL)
    last = data_5m.iloc[-1]
    price = last["Close"]
    prev_close = data_5m["Close"].iloc[-2]
    pct_change = (price - prev_close) / prev_close * 100
    day_high = last["High"]
    day_low = last["Low"]
    data_3m = ticker.history(period="3mo", interval="1d")
    high_3m = data_3m["High"].max()
    low_3m = data_3m["Low"].min()
    return price, pct_change, day_high, day_low, high_3m, low_3m

def get_time_icon():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if now.month in [12,1,2]:
        return "❄️"
    return "⏰"

def main():
    market_open = is_market_open()
    # ส่งข้อความถ้า run เอง หรือถ้าตลาดเปิด
    if market_open or True:  # True = run เองก็ส่งข้อความ
        price, pct_change, day_high, day_low, high_3m, low_3m = fetch_data()
        time_icon = get_time_icon()
        msg = (
            f"🔔 *Nvidia (NVDA)*\n\n"
            f"\n💵 ราคา: {price:.2f}  {pct_change:+.2f} ({pct_change:+.2f}%)\n\n"
            f"📈 High: {day_high:.2f}   📉 Low: {day_low:.2f}\n\n"
            f"📊 ช่วง 3 เดือน: {low_3m:.2f} - {high_3m:.2f}\n\n"
            f"{time_icon}"
        )
        send_telegram(msg)
    else:
        print("Market is closed. No message sent.")

if __name__ == "__main__":
    main()
