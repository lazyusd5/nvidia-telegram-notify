import yfinance as yf
import os
import requests
from datetime import datetime
import pytz


# ------------------------- CONFIG -------------------------

def get_env_float(name: str, default: float) -> float:
    """อ่านค่า env แบบปลอดภัย ถ้าไม่มีหรือว่าง → คืน default"""
    val = os.getenv(name, "").strip()

    if val == "":
        return default

    try:
        return float(val)
    except:
        return default


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID_BTC", "").strip()

VOL_THRESHOLD = get_env_float("VOL_THRESHOLD", 3.0)  # default = 3%

FORCE_RUN = os.getenv("FORCE_RUN", "false").lower() == "true"

SYMBOL = "NVDA"
TZ = pytz.timezone("US/Eastern")

# ------------------------- FUNCTIONS -------------------------

def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN / CHAT_ID ไม่มี → ข้ามการส่งข้อความ")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)


def get_price_data():
    try:
        ticker = yf.Ticker(SYMBOL)
        df = ticker.history(period="1d", interval="5m")
        if df.empty:
            return None
        return df
    except:
        return None


# ------------------------- MAIN LOGIC -------------------------

def main():
    df = get_price_data()
    if df is None:
        print("❌ ERROR: ไม่มีข้อมูลราคา")
        return

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    price = float(last["Close"])
    prev_price = float(prev["Close"])

    # % เปลี่ยนแปลงย้อนหลัง 5 นาที
    pct = ((price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    # ส่งเสมอถ้า FORCE_RUN = true
    if FORCE_RUN:
        msg = (
            f"📢 Manual Run NVDA Alert\n"
            f"Time: {now}\n"
            f"Price: {price:.2f}\n"
            f"Change (5m): {pct:.2f}%"
        )
        send_telegram(msg)
        print("✔ ส่งข้อความ manual แล้ว")
        return

    # เช็ค % สูงกว่าค่า threshold
    if abs(pct) >= VOL_THRESHOLD:
        arrow = "📈" if pct > 0 else "📉"
        msg = (
            f"{arrow} NVDA Alert ({SYMBOL})\n"
            f"Time: {now}\n"
            f"Price: {price:.2f}\n"
            f"Change (5m): {pct:.2f}% (trigger ≥ {VOL_THRESHOLD}%)"
        )
        send_telegram(msg)
        print("✔ ส่งแจ้งเตือนแล้ว")
    else:
        print(f"ℹ NVDA: {pct:.2f}% ยังไม่ถึง threshold {VOL_THRESHOLD}% → ไม่ส่งข้อความ")


# ------------------------- RUN -------------------------

if __name__ == "__main__":
    main()
