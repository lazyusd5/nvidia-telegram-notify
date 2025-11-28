import yfinance as yf
import os
import requests
from datetime import datetime
import pytz

# ------------------------- CONFIG -------------------------

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID_BTC", "").strip()
VOL_THRESHOLD = 3.0  # % change สำหรับ Volatility Alert

SYMBOL = "NVDA"
NY_TZ = pytz.timezone("America/New_York")

# ------------------------- FUNCTIONS -------------------------

def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN / CHAT_ID ว่าง → ข้ามการส่ง")
        print(msg)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)


def get_price_data():
    ticker = yf.Ticker(SYMBOL)
    df_5m = ticker.history(period="1d", interval="5m")
    df_3mo = ticker.history(period="3mo")

    if df_5m.empty or df_3mo.empty:
        return None

    last = df_5m.iloc[-1]
    prev = df_5m.iloc[-2] if len(df_5m) > 1 else last

    price = float(last["Close"])
    prev_price = float(prev["Close"])
    pct_change = ((price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

    day_high = df_5m["High"].max()
    day_low = df_5m["Low"].min()

    high_3m = df_3mo["High"].max()
    low_3m = df_3mo["Low"].min()

    return price, pct_change, day_high, day_low, high_3m, low_3m, last.name


def get_time_icon(dt):
    hour = dt.hour
    if 6 <= hour < 18:
        return "⏰ Eastern Daylight Time 🌞"
    else:
        return "⏰ Eastern Standard Time ❄️"

# ------------------------- MAIN -------------------------

def main():
    data = get_price_data()
    if not data:
        print("❌ ไม่มีข้อมูล")
        return

    price, pct_change, day_high, day_low, high_3m, low_3m, timestamp = data

    market_open = price != day_low  # ตลาดเปิด simplified check

    # Manual Run check
    is_manual_run = os.getenv("GITHUB_EVENT_NAME", "") == "workflow_dispatch"

    if not market_open and not is_manual_run:
        print("ℹ ตลาดปิด → ไม่ส่งข้อความ")
        return

    est_time = timestamp.tz_convert(NY_TZ)
    time_icon = get_time_icon(est_time)

    msg = (
        f"🔔 *Nvidia (NVDA)*\n\n"
        f"\n💵 ราคา: {price:.2f}  {pct_change:+.2f} ({pct_change:+.2f}%)\n\n"
        f"📈 High: {day_high:.2f}   📉 Low: {day_low:.2f}\n\n"
        f"📊 ช่วง 3 เดือน: {low_3m:.2f} - {high_3m:.2f}\n\n"
        f"{time_icon}"
    )
    send_telegram(msg)

    if abs(pct_change) >= VOL_THRESHOLD:
        arrow = "📈" if pct_change > 0 else "📉"
        vol_msg = (
            f"{arrow} *Volatility Alert — NVDA*\n\n"
            f"ราคาผันผวนเกิน {VOL_THRESHOLD}% ใน 5 นาที\n"
            f"ราคา: {price:.2f} ({pct_change:+.2f}%)\n\n"
            f"📈 High: {day_high:.2f}   📉 Low: {day_low:.2f}\n"
            f"📊 ช่วง 3 เดือน: {low_3m:.2f} - {high_3m:.2f}\n\n"
            f"{time_icon}"
        )
        send_telegram(vol_msg)


# ------------------------- RUN -------------------------
if __name__ == "__main__":
    main()
