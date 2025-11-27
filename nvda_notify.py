import yfinance as yf
import os
import requests

# Telegram token & Chat ID
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID_NVDA")  # ห้อง NVDA

# Volatility Threshold
VOL_THRESHOLD = 3  # % ราคาขยับ ≥3% แจ้งทันที

# ตรวจสอบ Manual run
FORCE_RUN = os.getenv("FORCE_RUN", "false").lower() == "true"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def get_nvda_price():
    ticker = yf.Ticker("NVDA")
    # ข้อมูล 1 วันย้อนหลังทุก 1 นาที สำหรับ High/Low 24h
    data_1d_1m = ticker.history(period="1d", interval="1m")
    # ข้อมูล 2 วันย้อนหลังทุก 1 วัน สำหรับ 24h change
    data_2d_daily = ticker.history(period="2d", interval="1d")
    if data_1d_1m.empty or data_2d_daily.empty:
        return None, None, None, None, None, None

    # ตรวจสอบว่าตลาดเปิดจริง / มีการซื้อขาย
    if data_1d_1m["Close"].iloc[-1] == data_2d_daily["Close"].iloc[-2]:
        return "CLOSED", None, None, None, None, None

    price = data_1d_1m["Close"].iloc[-1]
    day_high = data_1d_1m["High"].max()
    day_low = data_1d_1m["Low"].min()

    prev_24h = data_2d_daily["Close"].iloc[0]
    change_val_24h = price - prev_24h
    pct_change_24h = (change_val_24h / prev_24h) * 100

    return price, day_high, day_low, change_val_24h, pct_change_24h, data_1d_1m

def get_highlow_3m():
    ticker = yf.Ticker("NVDA")
    data = ticker.history(period="3mo")
    return data["High"].max(), data["Low"].min()

def main():
    result = get_nvda_price()
    if result[0] is None:
        send_telegram("❗ Error: ไม่พบข้อมูลราคาของ NVDA")
        return
    if result[0] == "CLOSED" and not FORCE_RUN:
        print("ตลาด NVDA ปิดวันนี้ / ไม่มีการซื้อขาย")
        return

    price, day_high, day_low, change_val_24h, pct_change_24h, data = result
    high_3m, low_3m = get_highlow_3m()

    # ข้อความ Telegram หลัก
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
