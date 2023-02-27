import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(df, period):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = abs(delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

ticker = "AAPL"
intervals = ['5m', '15m', '1h', '4h', '1d']
df = yf.download(ticker, interval=intervals[0], period="1d")

for interval in intervals:
    df_interval = df.resample(interval).last().dropna()
    rsi = calculate_rsi(df_interval, 14)
    df_interval['RSI'] = rsi
    print("RSI on {} time frame: \n{}".format(interval, df_interval['RSI'].tail()))

