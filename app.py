import time
import streamlit as st
import yfinance as yf
import pandas as pd
import schedule
import ollama
from datetime import datetime, timedelta

st.title("AI Stock Advisor")
logtxtbox = st.empty()
logtxt = '09:30:00'
logtxtbox.caption(logtxt)

apple_stock = yf.Ticker("AAPL")
goog_stock = yf.Ticker('GOOG')
ms_stock = yf.Ticker('MSFT')
dji_stock = yf.Ticker('^DJI')

apple_data = apple_stock.history(period="1d", interval="1m")
goog_data = goog_stock.history(period="1d", interval="1m")
ms_data = ms_stock.history(period="1d", interval="1m")
dow_data = dji_stock.history(period="1d", interval="1m")

ap_rolling_window = pd.DataFrame()
go_rolling_window = pd.DataFrame()
ms_rolling_window = pd.DataFrame()
dow_rolling_window = pd.DataFrame()

daily_high = float('-inf')
daily_low = float('inf')
buying_momentum = 0
selling_momentum = 0


def process_stock_update():
    global ap_rolling_window, apple_data, go_rolling_window, goog_data
    global ms_rolling_window, ms_data, dow_rolling_window, dow_data
    global daily_high, daily_low, buying_momentum, selling_momentum

    if not apple_data.empty:
        update_ap = apple_data.iloc[0].to_frame().T
        apple_data = apple_data.iloc[1:]

        ap_rolling_window = pd.concat([ap_rolling_window, update_ap], ignore_index=False)
        if len(ap_rolling_window) > 5:
            ap_rolling_window = ap_rolling_window.iloc[1:]

        calculate_insights(ap_rolling_window, dow_rolling_window)

        logtxtbox.caption(f"Processed update at {update_ap.index[0].strftime('%H:%M:%S')}")


def calculate_insights(window, dow_window):
    # Analysis logic goes here...
    st.write("Calculating Insights...")  # Placeholder for actual insights


schedule.every(10).seconds.do(process_stock_update)

while True:
    schedule.run_pending()
    time.sleep(1)