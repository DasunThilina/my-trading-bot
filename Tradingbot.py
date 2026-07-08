import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests

# --- වෙබ් පිටුවේ ප්‍රධාන සැකසුම් ---
st.set_page_config(page_title="Crypto Trading Bot", page_icon="🤖", layout="centered")
st.title("🤖 Live Crypto Trading Bot")
st.write("ඔබේ Exchange එක ආරක්ෂිතව සම්බන්ධ කරලා ලයිව් ට්‍රේඩින් ආරම්භ කරන්න.")
st.markdown("---")

# --- 1. Exchange සැකසුම් ---
st.subheader("🏦 1. Exchange සැකසුම්")
exchange_id = st.selectbox("Exchange එක තෝරන්න:", ["okx", "bybit", "binance"])
api_key = st.text_input("API Key:")
secret_key = st.text_input("Secret Key:", type="password")
password = st.text_input("Passphrase (OKX සඳහා පමණි, වෙනත් ඒවාට හිස්ව තබන්න):", type="password")
st.markdown("---")

# --- 2. ට්‍රේඩින් සැකසුම් (Trading Settings) ---
st.subheader("⚙️ 2. ට්‍රේඩින් සැකසුම් (Trading Settings)")
# කාසිය තේරීමට Dropdown එක
symbol = st.selectbox("Trade කරන Coin එක තෝරන්න (Symbol):", ["TRX/USDT", "BTC/USDT", "ETH/USDT", "SOL/USDT", "TON/USDT"])

# අවම මුදල $1 දක්වා වෙනස් කර ඇත
amount = st.number_input("එක් වරකට ට්‍රේඩ් කරන මුදල (Amount in USDT):", min_value=1.0, value=1.0, step=1.0)

# RSI අගයන් පරිශීලකයාට (User) වෙනස් කළ හැකි පරිදි සැකසීම
col1, col2 = st.columns(2)
with col1:
    rsi_buy = st.number_input("RSI Buy Level (මිලදී ගන්නා අවමය):", min_value=10, max_value=50, value=40)
with col2:
    rsi_sell = st.number_input("RSI Sell Level (විකුණන උපරිමය):", min_value=50, max_value=90, value=60)
st.markdown("---")

# --- 3. Telegram සැකසුම් ---
st.subheader("📱 3. Telegram දැනුම්දීම් සැකසුම්")
tg_bot_token = st.text_input("Telegram Bot Token:")
tg_chat_id = st.text_input("Telegram Chat ID:")

def send_telegram_message(message):
    """ටෙලිග්‍රෑම් වෙත පණිවිඩ යැවීමේ ශ්‍රිතය"""
    if tg_bot_token and tg_chat_id:
        url = f"https://api.telegram.org/bot{tg_bot_token}/sendMessage"
        payload = {"chat_id": tg_chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except:
            pass

st.markdown("---")

# --- 4. බොට් ක්‍රියාත්මක වීමේ කොටස (Bot Logic) ---
if st.button("▶ START BOT"):
    if not api_key or not secret_key:
        st.error("⚠️ කරුණාකර API Key සහ Secret Key ඇතුළත් කරන්න.")
    else:
        st.success("✅ බොට් සාර්ථකව ආරම්භ විය! පහතින් තොරතුරු යාවත්කාලීන වේවි.")
        
        # Exchange එකට සම්බන්ධ වීම
        exchange_params = {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        }
        if exchange_id == 'okx' and password:
            exchange_params['password'] = password
            
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class(exchange_params)
            
            placeholder = st.empty()
            
            while True:
                try:
                    # මාකට් එකේ දත්ත ලබා ගැනීම (1 minute chart)
                    bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
                    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # RSI ගණනය කිරීම
                    df['rsi'] = ta.rsi(df['close'], length=14)
                    
                    current_price = df['close'].iloc[-1]
                    current_rsi = df['rsi'].iloc[-1]
                    
                    # ඩෑෂ්බෝඩ් එකේ දත්ත පෙන්වීම
                    placeholder.info(f"🔍 මාකට් එක නිරීක්ෂණය කරමින් පවතී...\n\n**Coin:** {symbol}\n**දැනට මිල:** {current_price} USDT\n**දැනට RSI අගය:** {current_rsi:.2f}")
                    
                    # --- Buy Logic ---
                    if current_rsi < rsi_buy:
                        msg = f"🟢 BUY Signal: {symbol}\nPrice: {current_price}\nRSI: {current_rsi:.2f}"
                        send_telegram_message(msg)
                        
                        try:
                            buy_amount = amount / current_price # USDT ප්‍රමාණය කොයින් ගණනට හැරවීම
                            exchange.create_market_buy_order(symbol, buy_amount)
                            st.success(f"BUY Order සාර්ථකයි! ({amount} USDT)")
                        except Exception as e:
                            st.error(f"Buy Order එක දැමීමේදී දෝෂයක්: {e}")
                            
                        time.sleep(120) # මිලදී ගත් පසු විනාඩි 2ක් රැඳී සිටීම
                        
                    # --- Sell Logic ---
                    elif current_rsi > rsi_sell:
                        msg = f"🔴 SELL Signal: {symbol}\nPrice: {current_price}\nRSI: {current_rsi:.2f}"
                        send_telegram_message(msg)
                        
                        try:
                            # මිලදී ගත් ප්‍රමාණයම විකිණීම සඳහා
                            sell_amount = amount / current_price 
                            exchange.create_market_sell_order(symbol, sell_amount)
                            st.warning(f"SELL Order සාර්ථකයි!")
                        except Exception as e:
                            st.error(f"Sell Order එක දැමීමේදී දෝෂයක්: {e}")
                            
                        time.sleep(120) # විකුණූ පසු විනාඩි 2ක් රැඳී සිටීම
                        
                except Exception as e:
                    placeholder.warning(f"දත්ත ලබා ගැනීමේදී සුළු දෝෂයක්. නැවත උත්සාහ කරයි... Error: {e}")
                    
                time.sleep(15) # තත්පර 15කට වරක් මාකට් එක චෙක් කිරීම
                
        except Exception as e:
            st.error(f"Exchange එකට සම්බන්ධ වීමේදී දෝෂයක්. Keys සහ Passphrase නිවැරදි දැයි පරීක්ෂා කරන්න. Error: {e}")
