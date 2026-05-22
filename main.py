import requests
import time
import sys
import pandas as pd
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

print("--- SAHIL'S UNIVERSAL FREE CLOUD TERMINAL ---")

# ================= CONFIGURATION KEYS =================
TELEGRAM_TOKEN = '8616593561:AAEfLQBJKSU6c88vjdGbtuQ8FE3Poditsy0'
# ======================================================

# Fake Server to bypass Render's Free Port Scan
class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Sahil's Trading Bot is Running Live 24/7!")

def run_fake_server():
    server = HTTPServer(('0.0.0.0', 10000), FakeServer)
    server.serve_forever()

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return 50.0
    df = pd.DataFrame(prices, columns=['close'])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_on_demand_signal(user_input):
    coin = user_input.strip().replace("'", "").replace('"', '').replace("`", "").upper()
    if coin in ['XAUUSD', 'GOLD', 'PAXG']:
        symbol = 'PAXGUSDT'
    elif coin in ['XAGUSD', 'SILVER']:
        symbol = 'XAGUSDT'
    else:
        if not coin.endswith('USDT'):
            symbol = f"{coin}USDT"
        else:
            symbol = coin
            
    klines_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=50"
    try:
        response = requests.get(klines_url)
        if response.status_code != 200:
            return f"❌ Sahil bhai, Binance par '{symbol}' naam ka koi token nahi mila. Spelling check karo!"
        data = response.json()
        close_prices = [float(candle[4]) for candle in data]
        current_price = close_prices[-1]
        rsi_val = calculate_rsi(close_prices)
        
        if rsi_val <= 35:
            advice = "🟩 **BUY / LONG ZONE**\n⚡ Market ekdum sasta hai, dubki lagane ka best time hai!"
        elif rsi_val >= 65:
            advice = "🟥 **SHORT / SELL ZONE**\n⚡ Market overvalued hai, short ka mauka dhoondho!"
        else:
            advice = "🟨 **HOLD / NO-TRADE ZONE**\n⚡ Abhi beech mein hai, market ko direction lene do, door raho!"

        return (
            f"🔍 **SAHIL AI TRADING REPORT** 🔍\n\n"
            f"🪙 **Asset:** {symbol}\n"
            f"💰 **Live Price:** ${current_price:,.4f}\n"
            f"📊 **Current RSI:** {rsi_val:.2f}\n\n"
            f"🧭 **Suggestion:**\n{advice}"
        )
    except Exception as e:
        return f"❌ Error aaya bhai: {e}"

def reply_to_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

# Start Fake Port Server in a background thread
threading.Thread(target=run_fake_server, daemon=True).start()

# Telegram Message Polling Engine
offset = 0
while True:
    try:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=10"
        response = requests.get(tg_url).json()
        if "result" in response:
            for update in response["result"]:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_msg = update["message"]["text"].strip()
                    if user_msg.lower() == '/start':
                        reply_to_telegram(chat_id, "👋 Sahil bhai! Welcome. Coin ka naam bhejo (btc, eth, sol, bnb, xauusd)...")
                        continue
                    report = get_on_demand_signal(user_msg)
                    reply_to_telegram(chat_id, report)
    except Exception as e:
        pass
    time.sleep(1)
    
