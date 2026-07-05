import streamlit as st
import ccxt
import pandas as pd
import ta
import time
import requests # ටෙලිග්‍රෑම් සඳහා අලුතින් එකතු කළ ලයිබ්‍රරිය

st.set_page_config(page_title="Crypto Trading Bot", page_icon="🤖", layout="centered")
st.title("🤖 ස්වයංක්‍රීය ට්‍රේඩින් බොට්")
st.markdown("---")

# --- ටෙලිග්‍රෑම් මැසේජ් යැවීමේ ෆන්ක්ෂන් එක ---
def send_telegram_message(token, chat_id, message):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# --- දත්ත ලබාගන්නා කොටස ---
@st.cache_data 
def get_crypto_pairs(exchange_name):
    try:
        exchange_class = getattr(ccxt, exchange_name.lower())
        exchange = exchange_class()
        markets = exchange.load_markets() 
        return [symbol for symbol in markets.keys() if '/USDT' in symbol]
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

def get_current_price(exchange_name, symbol):
    try:
        exchange_class = getattr(ccxt, exchange_name.lower())
        exchange = exchange_class()
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception:
        return None

# --- 1. මූලික සැකසුම් ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("⚙️ මූලික සැකසුම්")
    exchange = st.selectbox("Exchange එක තෝරන්න:", ["Binance", "Bybit", "OKX"])
    market_type = st.selectbox("මාකට් එක (Market):", ["Spot Trading", "Futures Trading"])
    coin_list = get_crypto_pairs(exchange)
    coin = st.selectbox("කාසිය (Coin):", coin_list)
    trade_amount = st.number_input("එක් ට්‍රේඩ් එකක් සඳහා මුදල (USDT):", min_value=10, value=20)

with col2:
    st.subheader("📈 උපාය මාර්ග (Strategy)")
    strategy = st.selectbox("Strategy එක තෝරන්න:", ["RSI + MACD + EMA", "Only RSI", "Custom"])
    if market_type == "Futures Trading":
        leverage = st.slider("Leverage අගය:", min_value=1, max_value=50, value=10)
    st.markdown("**අවදානම් කළමනාකරණය (Risk Management)**")
    col_tp, col_sl = st.columns(2)
    with col_tp:
        take_profit = st.number_input("Take Profit (%):", value=1.50, step=0.1)
    with col_sl:
        stop_loss = st.number_input("Stop Loss (%):", value=0.75, step=0.1)

st.markdown("---")

# --- 2. Exchange API සහ Telegram සම්බන්ධතාවය ---
st.subheader("🔑 ගිණුම් සම්බන්ධතාව (API & Telegram)")
api_col1, api_col2, api_col3 = st.columns(3)
with api_col1:
    api_key = st.text_input("Exchange API Key:", type="password")
with api_col2:
    api_secret = st.text_input("Exchange Secret Key:", type="password")
with api_col3:
    if exchange == "OKX":
        api_passphrase = st.text_input("OKX Passphrase:", type="password")
    else:
        api_passphrase = None

# අලුත් ටෙලිග්‍රෑම් කොටු දෙක
tel_col1, tel_col2 = st.columns(2)
with tel_col1:
    tg_token = st.text_input("Telegram Bot Token:", type="password")
with tel_col2:
    tg_chat_id = st.text_input("Telegram Chat ID:", type="password")

st.markdown("---")

current_price = get_current_price(exchange, coin)
if current_price:
    st.metric(label=f"💲 {coin} වත්මන් මිල (Live Price)", value=f"${current_price:,}")
st.markdown("---")

# --- බොට් පාලනය ---
st.subheader("▶️ බොට් පාලනය")
col3, col4 = st.columns(2)

if 'is_running' not in st.session_state:
    st.session_state.is_running = False

with col3:
    if st.button("▶ START BOT", use_container_width=True, type="primary"):
        st.session_state.is_running = True
        st.success("✅ බොට් සාර්ථකව ආරම්භ විය!")
        
        # බොට් ස්ටාට් කළ ගමන් ටෙලිග්‍රෑම් එකට මැසේජ් එකක් යැවීම
        welcome_msg = f"🚀 *Trading Bot Started!*\n\n📊 Exchange: {exchange}\n🪙 Coin: {coin}\n💰 Live Price: ${current_price}"
        send_telegram_message(tg_token, tg_chat_id, welcome_msg)

with col4:
    if st.button("⏹ STOP BOT", use_container_width=True):
        st.session_state.is_running = False
        st.error("🛑 බොට් ක්‍රියා විරහිත කරන ලදී!")
        
        stop_msg = "🛑 *Trading Bot Stopped!*"
        send_telegram_message(tg_token, tg_chat_id, stop_msg)

if st.session_state.is_running:
    status_placeholder = st.empty() 
    for i in range(5): 
        if not st.session_state.is_running:
            break
        status_placeholder.info(f"🔄 වටය {i+1}: මාකට් එක විශ්ලේෂණය කරමින් පවතී...")
        time.sleep(2) 
        status_placeholder.success(f"✔️ වටය {i+1} සම්පූර්ණයි. (WAIT)")
        time.sleep(3)