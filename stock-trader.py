import streamlit as st
import yfinance as yf
import pandas as pd
import schedule
import ollama
from datetime import datetime, timedelta

#Streamlit UII
st.title("AI Stock Advisor")
logtxtbox = st.empty()
logtxt = '09:30:00'
logtxtbox.caption(logtxt)

#Fetching Historical data from Apple (APPL), Google (GOOG), Microsoft (MSFT), and Dow Jones (DJI)
apple_stock= yf.Ticker("AAPL")
goog_stock = yf.Ticker('GOOG')
ms_stock = yf.Ticker('MSFT')
dji_stock= yf.Ticker('^DJI')

apple_data = apple_stock.history(period = "1d", interval = "1m")
goog_data = goog_stock.history(period= "1d", interval = "1m")
ms_data = ms_stock.history(period = "1d", interval = "1m")
dow_data = dji_stock.history(period = "1d", interval=  "1m")


#Global variables to store rollling data for analysis
ap_rolling_window = pd.DataFrame()
go_rolling_window = pd.DataFrame()
ms_rolling_window = pd.DataFrame()
dow_rolling_window = pd.DataFrame()

#variables to track daily context
daily_high = float('-inf')
daily_low = float('inf')
buying_momentum = 0
selling_momentum = 0


#Function to process a new stock update every minute
def process_stock_update():
    global ap_rolling_window, apple_data, go_rolling_window, goog_data, ms_rolling_window, ms_data, dow_rolling_window, dow_data
    global daily_high, daily_low, buying_momentum, selling_momentum

    if not apple_data.empty and not goog_data.empty and not ms_data.empty and not dow_data.empty:
        #Simulate receiving a new data points
        update_ap = apple_data.iloc[0].to_frame().T
        update_go = goog_data.iloc[0].to_frame().T
        update_ms = ms_data.iloc[0].to_frame().T
        update_dow = dow_data.iloc[0].to_frame().T
        time_str_ap = update_ap.index[0].time()
        time_str_go  = update_go.index[0].time()
        time_str_ms = update_ms.index[0].time()
        time_str_dow = update_dow.index[0].time()
        print(time_str_ap)
        print(time_str_go)
        print(time_str_ms)
        print(time_str_dow)
        data_ap = apple_data.iloc[1:] #safely removes the first row without causing index issues
        data_go = goog_data.iloc[1:]
        data_ms = ms_data.iloc[1:]
        data_dow = dow_data.iloc[1:]

        #Appending the new data points to the rolling windows
        ap_rolling_window = pd.concat([ap_rolling_window, update_ap], ignore_index= False)
        go_rolling_window = pd.concat([go_rolling_window, update_go], ignore_index= False)
        ms_rolling_window = pd.concat([ms_rolling_window, update_ms], ignore_index= False)
        dow_rolling_window = pd.concat([dow_rolling_window, update_dow], ignore_index= False)

        #update daily high and and lows for each
        ap_daily_high = max(daily_high, update_ap['Close'].values[0])
        ap_daily_low = max(daily_low, update_ap['Close'].values[0])
        go_daily_high = max(daily_high, update_go['Close'].values[0])
        go_daily_low = max(daily_low, update_go['Close'].values[0])
        ms_daily_high = max(daily_high, update_ms['Close'].values[0])
        ms_daily_low = max(daily_low, update_ms['Close'].values[0])

        #Calculate momentum based on price changes
        if len(ap_rolling_window) >= 2:
            price_change = update_ap['Close'].values[0] - ap_rolling_window['Close'].iloc[-2]
            if price_change > 0:
                buying_momentum += price_change
            else:
                selling_momentum += abs(price_change)

        if len(go_rolling_window) >= 2:
            price_change = update_go['Close'].values[0] - go_rolling_window['Close'].iloc[-2]
            if price_change > 0:
                buying_momentum += price_change
            else:
                selling_momentum += abs(price_change)

        if len(ms_rolling_window) >= 2:
            price_change = update_ms['Close'].values[0] - ms_rolling_window['Close'].iloc[-2]
            if price_change > 0:
                buying_momentum += price_change
            else:
                selling_momentum += abs(price_change)


        if len(dow_rolling_window) >= 2:
            price_change = update_dow['Close'].values[0] - dow_rolling_window['Close'].iloc[-2]
            if price_change > 0:
                buying_momentum += price_change
            else:
                selling_momentum += abs(price_change)

        #Limiting the rolling window to 5 minures for moving average

        if len(ap_rolling_window > 5):
            ap_rolling_window =  ap_rolling_window.iloc[1:]

        if len(go_rolling_window > 5):
            go_rolling_window = go_rolling_window.iloc[1:]

        if len(ms_rolling_window > 5):
            ms_rolling_window = ms_rolling_window.iloc[1:]

        if len(dow_rolling_window > 5):
            dow_rolling_window = dow_rolling_window.iloc[1:]

        # Calculating insights (moving averages, Bollinger Bands, RSI, etc.)
        #calculate_insights(ap_rolling_window, go_rolling_window, ms_rolling_window, dow_rolling_window )



def get_market_open_duration(window):
    # Extract current time from the last element of the window
    current_time = window.index[-1].time()  # Returns a datetime.time object
    
    # Get the previous trading day's date
    previous_trading_day = datetime.today() - timedelta(days=1)
    
    # Combine the previous trading day with the current time
    current_datetime = datetime.combine(previous_trading_day, current_time)
    
    # Define the market opening time as 09:30:00 on the previous trading day
    market_start_time = datetime.combine(previous_trading_day, datetime.strptime("09:30:00", "%H:%M:%S").time())
    
    # Calculate the duration the market has been open in minutes
    market_open_duration = (current_datetime - market_start_time).total_seconds() / 60  # in minutes
    
    return market_open_duration

