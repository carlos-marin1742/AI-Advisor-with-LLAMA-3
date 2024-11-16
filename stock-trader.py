import time
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



# Function to calculate insights like moving averages and trends
def calculate_insights(window, dow_window):
    if len(window) >= 5:
        # Calculate 5-minute rolling average of the 'Close' prices
        rolling_avg = window['Close'].rolling(window=5).mean().iloc[-1]

        # Calculate price change and volume change
        price_change = window['Close'].iloc[-1] - window['Close'].iloc[-2] if len(window) >= 2 else 0
        volume_change = window['Volume'].iloc[-1] - window['Volume'].iloc[-2] if len(window) >= 2 else 0

        # Calculate DOW price change and volume change
        dow_price_change = dow_window['Close'].iloc[-1] - dow_window['Close'].iloc[-2] if len(dow_window) >= 2 else 0
        dow_volume_change = dow_window['Volume'].iloc[-1] - dow_window['Volume'].iloc[-2] if len(dow_window) >= 2 else 0
    
        # Calculate Exponential Moving Average (EMA) and Bollinger Bands (with a 5-period window)
        ema = window['Close'].ewm(span=5, adjust=False).mean().iloc[-1]
        std = window['Close'].rolling(window=5).std().iloc[-1]
        bollinger_upper = rolling_avg + (2 * std)
        bollinger_lower = rolling_avg - (2 * std)

        # Calculate Relative Strength Index (RSI) if there are enough periods (14 is typical)
        delta = window['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=1).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else float('nan')
        rsi = 100 - (100 / (1 + rs))

        calculate_insights(ap_rolling_window, go_rolling_window, ms_rolling_window, dow_rolling_window )

        # Calculate Dow Jones index rolling average
        dow_rolling_avg = dow_window['Close'].rolling(window=5).mean().iloc[-1]
        
        market_open_duration = get_market_open_duration(window)


    # Function to calculate insights like moving averages and trends
def calculate_insights(window, dow_window):
    if len(window) >= 5:
        # Calculate 5-minute rolling average of the 'Close' prices
        rolling_avg = window['Close'].rolling(window=5).mean().iloc[-1]

        # Calculate price change and volume change
        price_change = window['Close'].iloc[-1] - window['Close'].iloc[-2] if len(window) >= 2 else 0
        volume_change = window['Volume'].iloc[-1] - window['Volume'].iloc[-2] if len(window) >= 2 else 0

        # Calculate DOW price change and volume change
        dow_price_change = dow_window['Close'].iloc[-1] - dow_window['Close'].iloc[-2] if len(dow_window) >= 2 else 0
        dow_volume_change = dow_window['Volume'].iloc[-1] - dow_window['Volume'].iloc[-2] if len(dow_window) >= 2 else 0
    
        # Calculate Exponential Moving Average (EMA) and Bollinger Bands (with a 5-period window)
        ema = window['Close'].ewm(span=5, adjust=False).mean().iloc[-1]
        std = window['Close'].rolling(window=5).std().iloc[-1]
        bollinger_upper = rolling_avg + (2 * std)
        bollinger_lower = rolling_avg - (2 * std)

        # Calculate Relative Strength Index (RSI) if there are enough periods (14 is typical)
        delta = window['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=1).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else float('nan')
        rsi = 100 - (100 / (1 + rs))

        # Calculate Dow Jones index rolling average
        dow_rolling_avg = dow_window['Close'].rolling(window=5).mean().iloc[-1]
        
        market_open_duration = get_market_open_duration(window)

                # Print the calculated insights
        print(f"5-minute Rolling Average: {rolling_avg:.2f}")
        print(f"EMA: {ema:.2f}")
        print(f"RSI: {rsi:.2f}")
        print(f"Bollinger Upper Band: {bollinger_upper:.2f}, Lower Band: {bollinger_lower:.2f}")
        print(f"Price Change: {price_change:.2f}")
        print(f"Volume Change: {volume_change}")
        print(f"DOW Price Change: {dow_price_change:.2f}")
        print(f"DOW Volume Change: {dow_volume_change}")
        print(f"Dow Jones 5-minute Rolling Average: {dow_rolling_avg:.2f}")
        print(f"Daily High: {daily_high:.2f}, Daily Low: {daily_low:.2f}")
        print(f"Buying Momentum: {buying_momentum:.2f}, Selling Momentum: {selling_momentum:.2f}")
        print(f"Market has been open for {market_open_duration:.2f} minutes")
        

        if int(market_open_duration) % 5 == 0:  # Trigger LLM every 5 minutes
            get_natural_language_insights(
                rolling_avg, ema, rsi, bollinger_upper, bollinger_lower,
                price_change, volume_change, dow_rolling_avg, market_open_duration, dow_price_change, dow_volume_change, daily_high, daily_low, buying_momentum, selling_momentum, window.index[-1].time().strftime("%H:%M:%S")
            )

# Function to generate natural language insights using Ollama
def get_natural_language_insights(
    rolling_avg, ema, rsi, bollinger_upper, bollinger_lower,
    price_change, volume_change, dow_rolling_avg, market_open_duration, dow_price_change, dow_volume_change, daily_high, daily_low, buying_momentum, selling_momentum, timestamp
    ):

        prompt = f"""
    You are a professional stock broker. Apple's stock has a 5-minute rolling average of {rolling_avg:.2f}.
    The Exponential Moving Average (EMA) is {ema:.2f}, and the Relative Strength Index (RSI) is {rsi:.2f}.
    The Bollinger Bands are set with an upper band of {bollinger_upper:.2f} and a lower band of {bollinger_lower:.2f}.
    The price has changed by {price_change:.2f}, and the volume has shifted by {volume_change}.
    The DOW price has changed by {dow_price_change:.2f}, and the volume has shifted by {dow_volume_change}.
    Meanwhile, the Dow Jones index has a 5-minute rolling average of {dow_rolling_avg:.2f}.
    The market has been open for {market_open_duration:.2f} minutes.
    Today's high was {daily_high:.2f} and low was {daily_low:.2f}.
    The buying momentum is {buying_momentum:.2f} and selling momentum is {selling_momentum:.2f}.
    Based on this data, provide insights into the current stock trend and the general market sentiment.
    The insights should not be longer than 100 words and should not have an introduction.
    """
response = ollama.chat(
            model="llama3.1",            
            messages=[{"role": "user", "content": prompt}] # type: ignore
        )
response_text = response['message']['content'].strip()
message = st.chat_message("assistant")
message.write(timestamp) # type: ignore
message.write(response_text)
print("Natural Language Insight:", response_text)

# Schedule job to simulate receiving updates every minute
schedule.every(10).seconds.do(process_stock_update)  


message = st.chat_message("assistant")
message.write("Starting real-time simulation for AAPL stock updates. First update will be processed in 5 minutes...")    
# Run the scheduled jobs
print("Starting real-time simulation for AAPL stock updates...")
while True:
    schedule.run_pending()
    time.sleep(1)