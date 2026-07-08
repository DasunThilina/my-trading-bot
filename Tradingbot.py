import streamlit as st
import ccxt
import time
import pandas as pd
import requests

# වෙබ් පිටුවේ ප්‍රධාන සැකසුම් (Page Configuration)
st.set_page_config(page_title="Crypto Trading Bot", page_icon="🤖", layout="centered")
st.title("🤖 Live Crypto Trading Bot")
st.write("ඔයාගේ Exchange එක ආරක්ෂිතව සම්බන්ධ කරලා ලයිව් ට්‍රේඩින් ආරම්භ කරන්න.")

# බොට් ක්‍රියාත්මක වන තත්ත්වය පාලනය කිරීමට (Session State)
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# ටෙලිග්‍රෑම් පණිවිඩ යවන ශ්‍රිතය (Telegram Notification Function)
def send_telegram_message(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Telegram පණිවිඩය යැවීමේදී දෝෂයක්: {e}")

# RSI අගය ගණනය කරන ශ්‍රිතය
def calculate_rsi(exchange, symbol, timeframe='15m', period=14):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except Exception as e:
        st.error(f"RSI දත්ත ලබාගැනීමේ දෝෂයක්: {e}")
        return None

# --- UI සැකසුම් (User Interface) ---
st.header("⚙️ බොට් සැකසුම් (Settings)")

# Exchange එක තෝරාගැනීම
exchange_name = st.selectbox("Exchange එක තෝරන්න:", ["Bybit", "OKX", "Binance"])

# API Keys ඇතුළත් කිරීමේ කොටු
api_key = st.text_input("Exchange API Key එක ඇතුළත් කරන්න:", type="password")
secret_key = st.text_input("Exchange Secret Key එක ඇතුළත් කරන්න:", type="password")

# OKX තේරුවොත් විතරක් Passphrase කොටුව පෙන්වීම
passphrase = ""
if exchange_name == "OKX":
    passphrase = st.text_input("OKX Passphrase (API Password) එක ඇතුළත් කරන්න:", type="password")

st.subheader("📱 Telegram සම්බන්ධතාවය")
tg_token = st.text_input("Telegram Bot Token එක ඇතුළත් කරන්න:", type="password")
tg_chat_id = st.text_input("Telegram Chat ID එක ඇතුළත් කරන්න:")

st.subheader("💰 ට්‍රේඩින් උපදෙස්")
symbol = st.text_input("ਟ්‍රේਡ කරන්න ඕන කාසිය (Symbol):", value="BTC/USDT")
amount = st.number_input("එක් වරකට ට්‍රේඩ් කරන මුදල (Amount in USDT):", min_value=1.0, value=1.0, step=1.0)

# --- බොට් පාලන බොත්තම් (Bot Controls) ---
st.header("▶️ බොට් පාලනය (Bot Control)")
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ START BOT", disabled=st.session_state.is_running):
        if not api_key or not secret_key or not tg_token or not tg_chat_id or (exchange_name == "OKX" and not passphrase):
            st.error("කරුණාකර සියලුම විස්තර සහ API Keys නිවැරදිව ඇතුළත් කරන්න!")
        else:
            st.session_state.is_running = True
            st.rerun()

with col2:
    if st.button("⏹ STOP BOT", disabled=not st.session_state.is_running):
        st.session_state.is_running = False
        st.rerun()

# --- ලයිව් ට්‍රේඩින් ලූප් එක (Live Trading Loop) ---
if st.session_state.is_running:
    st.success("බොට් සාර්ථකව ආරම්භ විය! දැන් පසුබිමෙන් ක්‍රියාත්මක වේ.")
    
    status_box = st.empty()
    log_box = st.empty()
    
    # Exchange එක සක්‍රීය කිරීම
    try:
        exchange_class = getattr(ccxt, exchange_name.lower())
        exchange_params = {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        }
        # OKX සඳහා Passphrase එක එකතු කිරීම
        if exchange_name == "OKX":
            exchange_params['password'] = passphrase
            
        exchange = exchange_class(exchange_params)
        
    except Exception as e:
        st.error(f"Exchange එකට සම්බන්ධ වීමට නොහැක: {e}")
        st.session_state.is_running = False

    # අඛණ්ඩව දුවන ලූප් එක (තත්පර 60න් 60ට මාකට් එක බලයි)
    iteration = 1
    while st.session_state.is_running:
        status_box.info(f"🔄 වටය {iteration}: මාකට් එක විශ්ලේෂණය කරමින් පවතී...")
        
        # RSI අගය ලබා ගැනීම
        rsi_val = calculate_rsi(exchange, symbol)
        
        if rsi_val is not None:
            log_box.write(f"📊 වත්මන් RSI අගය ({symbol}): {rsi_val:.2f}")
            
            # --- මිලදී ගැනීමේ තීරණය (BUY LOGIC) ---
            if rsi_val < 40:
                try:
                    status_box.warning("🚨 RSI 40 ට වඩා අඩුයි! මිලදී ගැනීමේ ඕඩරයක් (BUY) යවමින්...")
                    
                    # ඇත්තටම Exchange එකට ඕඩර් එක යැවීම
                    order = exchange.create_market_buy_order(symbol, amount)
                    
                    msg = f"🟢 [BUY ORDER SUCCESS]\n• Exchange: {exchange_name}\n• Coin: {symbol}\n• Amount: {amount} USDT\n• RSI: {rsi_val:.2f}"
                    send_telegram_message(tg_token, tg_chat_id, msg)
                    st.toast("Buy Order එක සාර්ථකයි!", icon="🟢")
                except Exception as e:
                    st.error(f"Buy Order එක දැමීමේදී ප්‍රශ්නයක්: {e}")
                    send_telegram_message(tg_token, tg_chat_id, f"❌ Buy Order Failed: {e}")
            
            # --- විකිණීමේ තීරණය (SELL LOGIC) ---
            elif rsi_val > 65:
                try:
                    status_box.warning("🚨 RSI 65 ට වඩා වැඩියි! විකිණීමේ ඕඩරයක් (SELL) යවමින්...")
                    
                    # ඇත්තටම Exchange එකට ඕඩර් එක යැවීම
                    order = exchange.create_market_sell_order(symbol, amount)
                    
                    msg = f"🔴 [SELL ORDER SUCCESS]\n• Exchange: {exchange_name}\n• Coin: {symbol}\n• RSI: {rsi_val:.2f}"
                    send_telegram_message(tg_token, tg_chat_id, msg)
                    st.toast("Sell Order එක සාර්ථකයි!", icon="🔴")
                except Exception as e:
                    st.error(f"Sell Order එක දැමීමේදී ප්‍රශ්නයක්: {e}")
                    send_telegram_message(tg_token, tg_chat_id, f"❌ Sell Order Failed: {e}")
        
        iteration += 1
        time.sleep(60)  # විනාඩියක් (තත්පර 60ක්) නිහඬව සිට නැවත මාකට් එක බලයි

    status_box.warning("🛑 බොට් සම්පූර්ණයෙන්ම නතර කරන ලදී.")
