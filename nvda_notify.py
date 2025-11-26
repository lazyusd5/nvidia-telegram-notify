import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import pytz
import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg, image_path=None):
    if image_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {"photo": open(image_path, "rb")}
        data = {"chat_id": CHAT_ID, "caption": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, files=files)
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data)

def get_price():
    ticker = yf.Ticker("NVDA")
    data = ticker.history(period="5d", interval="1h")
    if data.empty or len(data) < 2:
        return None
    latest = data['Close'].iloc[-1]
    previous = data['Close'].iloc[-2]
    change = latest - previous
    percent = (change/previous)*100

    # เลือกข้อมูลของวันวันนี้ (NY time)
    ny = pytz.timezone("America/New_York")
    today_ny = datetime.datetime.now(ny).date()
    today_data = data[data.index.date == today_ny]

    day_high = today_data['High'].max()
    day_low = today_data['Low'].min()

    return latest, change, percent, day_high, day_low, data

def plot_graph(data):
    plt.figure(figsize=(8,4))
    plt.plot(data.index, data['Close'], marker='o', linestyle='-')
    plt.title("NVDA Stock Price (Last 5 Days)")
    plt.xlabel("Date/Time (NY)")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    path = "nvda_chart.png"
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path

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
    now_str = now_ny.strftime("%Y-%m-%d %H:%M:%S ET")  # เวลา NY

    if not market_open_now():
        print(f"ตลาดยังไม่เปิด ({now_str}) → ไม่ส่ง Telegram")
        return

    result = get_price()
    if result is None:
        send_telegram(f"❗ ไม่พบข้อมูลราคาหุ้น NVDA ({now_str})")
        return

    latest, change, percent, day_high, day_low, data = result
    msg = (
        "🔔 *NVIDIA (NVDA)*\n\n"
        f"⏰ เวลา NY: {now_str}\n"
        f"💵 ราคา: {latest:.2f} "
        f"{'+' if change>=0 else ''}{change:.2f} "
        f"({'+' if percent>=0 else ''}{percent:.2f}%)\n"
        f"📈 High วันนี้: {day_high:.2f}  📉 Low วันนี้: {day_low:.2f}"
    )

    chart_path = plot_graph(data)
    send_telegram(msg, chart_path)

if __name__ == "__main__":
    main()
