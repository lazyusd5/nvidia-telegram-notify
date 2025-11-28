import os
import yfinance as yf
import requests
from datetime import datetime
import pytz

# ------------------------- CONFIG -------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ใส่ chat id ของคุณ
SYMBOL = "NVDA"
TIMEZONE = "US/Eastern"
INTERVAL = "5m"

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
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now <= close_time

def fetch_data():
    ticker = yf.Ticker(SYMBOL)
    # ข้อมูลแท่ง 5m ล่าสุด
    data_5m = ticker.history(period="1d", interval=INTERVAL)
    last = data_5m.iloc[-1]
    price = last["Close"]
    prev_close = data_5m["Close"].iloc[-2]
    pct_change = (price - prev_close) / prev_close * 100

    # Day's Range
    day_high = last["High"]
    day_low = last["Low"]

    # 52 Week Range
    info = ticker.info
    week_52_high = info.get("fiftyTwoWeekHigh", 0)
    week_52_low = info.get("fiftyTwoWeekLow", 0)

    return price, pct_change, day_high, day_low, week_52_high, week_52_low

def get_time_icon():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if now.month in [12,1,2]:
        return "❄️"
    return "⏰"

# ------------------------- MAIN -------------------------
def main():
    market_open = is_market_open()
    # ส่งข้อความได้เลยถ้ากด run เอง หรือถ้าตลาดเปิด
    if market_open or True:
        price, pct_change, day_high, day_low, week_52_high, week_52_low = fetch_data()
        time_icon = get_time_icon()

        # ข้อความ Telegram ตามฟอร์แมตที่คุณให้
        msg = (
            f"🔔 *Nvidia (NVDA)*\n\n"
            f"💵 ราคา: *{price:.2f}*  {pct_change:+.2f} ({pct_change:+.2f}%) \n\n"
            f"📈 Day's Range : {day_low:.2f} - {day_high:.2f} \n\n"
            f"📊 52 Week Range : {week_52_low:.2f} - {week_52_high:.2f} \n\n"
            f"{time_icon}"
        )
        send_telegram(msg)
    else:
        print("Market is closed. No message sent.")

if __name__ == "__main__":
    main()
