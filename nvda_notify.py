import yfinance as yf
import requests
import pytz
from datetime import datetime, timedelta
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# -------------------------------
# 🔹 เวลา New York พร้อมชื่อเต็มและ icon ฤดู
# -------------------------------
def get_market_time():
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)

    if now.dst() != timedelta(0):
        zone = "Eastern Daylight Time 🌞"
    else:
        zone = "Eastern Standard Time ❄️"

    return now, zone

# -------------------------------
# 🔹 ตรวจสอบว่าตลาดเปิด
# -------------------------------
def is_market_open():
    now, _ = get_market_time()
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close

# -------------------------------
# 🔹 ส่งข้อความ Telegram
# -------------------------------
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# -------------------------------
# 🔹 โหลดข้อมูลหุ้น
# -------------------------------
def get_stock_data():
    ticker = yf.Ticker("NVDA")
    data = ticker.history(period="90d")

    last = data["Close"].iloc[-1]
    prev = data["Close"].iloc[-2]
    change = last - prev
    pct = (change / prev) * 100

    day_high = data["High"].iloc[-1]
    day_low = data["Low"].iloc[-1]

    high_3m = data["High"].max()
    low_3m = data["Low"].min()

    # High/Low 30 วัน
    data_30 = ticker.history(period="30d")
    high_30 = data_30["High"].max()
    low_30 = data_30["Low"].min()

    return last, change, pct, day_high, day_low, high_3m, low_3m, high_30, low_30

# -------------------------------
# 🔹 ตรวจสอบแจ้งเตือน High/Low 30 วัน
# -------------------------------
def check_special_alerts(price, high_30, low_30):
    alerts = []
    if price >= high_30:
        alerts.append(
            f"⚠️ *Breakout Alert — NVDA*\n\n"
            f"ราคาแตะระดับสูงสุดรอบ 30 วัน\nHigh 30 วัน: {high_30:.2f}\n"
            f"ราคา: {price:.2f}"
        )
    if price <= low_30:
        alerts.append(
            f"⚠️ *Support Alert — NVDA*\n\n"
            f"ราคาแตะระดับต่ำสุดรอบ 30 วัน\nLow 30 วัน: {low_30:.2f}\n"
            f"ราคา: {price:.2f}"
        )
    # ใกล้ High / Low ไม่เกิน 1%
    if 0 < (high_30 - price) <= high_30 * 0.01:
        alerts.append(
            f"⚠️ ราคาเข้าใกล้ High 30 วันภายใน 1%\nHigh 30 วัน: {high_30:.2f}\n"
            f"ราคา: {price:.2f}"
        )
    if 0 < (price - low_30) <= low_30 * 0.01:
        alerts.append(
            f"⚠️ ราคาเข้าใกล้ Low 30 วันภายใน 1%\nLow 30 วัน: {low_30:.2f}\n"
            f"ราคา: {price:.2f}"
        )
    return alerts

# -------------------------------
# 🔹 ส่งรายงานหลัก
# -------------------------------
def send_hourly_report():
    price, change, pct, day_high, day_low, high_3m, low_3m, high_30, low_30 = get_stock_data()
    now, zone = get_market_time()

    msg = (
        "🔔 *Nvidia (NVDA)*\n\n"
        f"💵 ราคา: *{price:.2f}*  {change:+.2f} ({pct:+.2f}%)\n\n"
        f"📈 High: {day_high:.2f}    📉 Low: {day_low:.2f}\n"
        f"📊 ช่วง 3 เดือน: {low_3m:.2f} - {high_3m:.2f}\n\n"
        f"⏰ เวลา: {now.strftime('%I:%M %p')}\n"
        f"{zone}"
    )

    send_message(msg)

    # ส่งแจ้งเตือนพิเศษ High/Low 30 วัน
    alerts = check_special_alerts(price, high_30, low_30)
    for alert in alerts:
        send_message(alert)

# -------------------------------
# 🔹 MAIN
# -------------------------------
def main():
    if is_market_open():
        send_hourly_report()
    else:
        # ถ้า manual run ส่งได้แม้ตลาดปิด
        now, zone = get_market_time()
        send_message(f"⚠️ ตลาดปิดอยู่ แต่คุณกด Run เอง\nเวลา: {now.strftime('%I:%M %p')} {zone}")
        send_hourly_report()


if __name__ == "__main__":
    main()
