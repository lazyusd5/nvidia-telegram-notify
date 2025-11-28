import yfinance as yf
import os
import requests
from datetime import datetime
import pytz

# Telegram token & Chat ID
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID_NVDA")

# Volatility Threshold (เช่น 3)
VOL_THRESHOLD = float(os.getenv("VOL_THRESHOLD", "3"))

# สำหรับส่งข้อความทุกครั้งเมื่อกด Run
FORCE_RUN = os.getenv("FORCE_RUN", "false").lower() == "true"

# Timezone ตลาดหุ้นสหรัฐ
NY_TZ = pytz.timezone("America/New_York")


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)


def get_nvda_data():
    ticker = yf.Ticker("NVDA")

    # 5m data เบาขึ้นมาก
    data_1d_5m = ticker.history(period="1d", interval="5m")
    # ใช้ข้อมูล 2 วันย้อนหลัง เพื่อให้ดูราคาเดิม 24 ชั่วโมงก่อน
    data_2d_daily = ticker.history(period="2d", interval="1d")

    if data_1d_5m.empty or data_2d_daily.empty:
        return None, None, None, None, None

    # ราคาปิดเมื่อวาน
    prev_close = data_2d_daily["Close"].iloc[-2]

    # ราคาปัจจุบัน
    price = data_1d_5m["Close"].iloc[-1]

    # เช็คตลาดเปิด (ถ้า price ≠ prev_close = มีการซื้อขาย)
    market_open = price != prev_close

    # High / Low 24 ชั่วโมงจาก 5m data
    day_high = data_1d_5m["High"].max()
    day_low = data_1d_5m["Low"].min()

    # 24h change
    change_val = price - prev_close
    pct_change = (change_val / prev_close) * 100

    return price, day_high, day_low, change_val, pct_change, market_open


def get_highlow_3m():
    ticker = yf.Ticker("NVDA")
    data = ticker.history(period="3mo")
    return data["High"].max(), data["Low"].min()


def main():
    data = get_nvda_data()
    if data[0] is None:
        send_telegram("❗ Error: ไม่พบข้อมูลราคาของ NVDA")
        return

    price, day_high, day_low, change_val_24h, pct_change_24h, market_open = data
    high_3m, low_3m = get_highlow_3m()

    # ❗ ไม่ส่งถ้าตลาดปิด (ยกเว้น manual run)
    if not market_open and not FORCE_RUN:
        print("ตลาด NVDA ปิดอยู่ ไม่ส่งข้อความ")
        return

    # สร้างข้อความหลักทุก 6 นาที (ตาม GitHub Actions)
    msg = (
        f"🔔 *Nvidia (NVDA)*\n\n"
        f"💵 ราคา: *{price:,.2f}*\n"
        f"เปลี่ยน 24 hr. {change_val_24h:+,.2f} ({pct_change_24h:+.2f}%)\n\n"
        f"📈 High (24h): {day_high:,.2f}\n"
        f"📉 Low (24h): {day_low:,.2f}\n"
        f"📊 ช่วง 3 เดือน: {high_3m:,.2f} - {low_3m:,.2f}\n"
    )

    send_telegram(msg)

    # Volatility Alert
    if abs(pct_change_24h) >= VOL_THRESHOLD:
        vol_msg = (
            f"⚡ *Volatility Alert — NVDA*\n\n"
            f"ราคาผันผวนเกิน {VOL_THRESHOLD}% ใน 24 ชั่วโมง\n"
            f"ราคา: {price:,.2f} ({pct_change_24h:+.2f}%)\n\n"
            f"📈 High (24h): {day_high:,.2f}\n"
            f"📉 Low (24h): {day_low:,.2f}\n"
            f"📊 ช่วง 3 เดือน: {high_3m:,.2f} - {low_3m:,.2f}"
        )
        send_telegram(vol_msg)


if __name__ == "__main__":
    main()
