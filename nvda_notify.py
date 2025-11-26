import yfinance as yf
import datetime
import pytz
import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def get_price():
    ticker = yf.Ticker("NVDA")
    # ข้อมูลย้อนหลัง 5 วัน สำหรับราคาล่าสุด
    data = ticker.history(period="5d", interval="1h")
    if data.empty or len(data) < 2:
        return None

    latest = data['Close'].iloc[-1]
    previous = data['Close'].iloc[-2]
    change = latest - previous
    percent = (change/previous)*100

    # High/Low ของวันปัจจุบัน
    ny = pytz.timezone("America/New_York")
    today_ny = datetime.datetime.now(ny).date()
    today_data = data[data.index.date == today_ny]
    day_high = today_data['High'].max()
    day_low = today_data['Low'].min()

    # High/Low ของ 3 เดือนย้อนหลัง
    data_3mo = ticker.history(period="3mo", interval="1d")
    high_3mo = data_3mo['High'].max()
    low_3mo = data_3mo['Low'].min()

    return latest, change, percent, day_high, day_low, high_3mo, low_3mo

def market_open_now():
    ny = pytz.timezone("America/New_York")
    now_ny = datetime.datetime.now(ny)
    weekday = now_ny.weekday()  # 0=Mon ... 4=Fri
    if weekday >= 5:
        return False
    open_time = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now_ny <= close_time

def main():
    ny = pytz.timezone("America/New_York")
    now_ny = datetime.datetime.now(ny)
    now_str = now_ny.strftime("%Y-%m-%d %H:%M:%S ET")

    if not market_open_now():
        print(f"ตลาดยังไม่เปิด ({now_str}) → ไม่ส่ง Telegram")
        return

    result = get_price()
    if result is None:
        send_telegram(f"❗ ไม่พบข้อมูลราคาหุ้น NVDA ({now_str})")
        return

    latest, change, percent, day_high, day_low, high_3mo, low_3mo = result
    msg = (
        "🔔 *NVDA Hourly Alert*\n\n"
        f"⏰ เวลา NY: {now_str}\n"
        f"💵 ราคา: {latest:.2f} "
        f"{'+' if change>=0 else ''}{change:.2f} "
        f"({'+' if percent>=0 else ''}{percent:.2f}%)\n"
        f"📈 High: {day_high:.2f}  📉 Low: {day_low:.2f}\n"
        f"📊 ช่วง 3 เดือน: {low_3mo:.2f} - {high_3mo:.2f}"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()
