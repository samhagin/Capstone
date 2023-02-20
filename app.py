from flask import Flask, Response, render_template, request, redirect, url_for, session
import pymysql
import configparser
import plotly.graph_objs as go
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from io import BytesIO
import base64, requests, json, plotly, re
from tradingview_ta import TA_Handler, Interval, Exchange
import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config['Polygon']['api_key']

app = Flask(__name__)


# Connect to the database
connection = pymysql.connect(
    host=config['MySQL_config']['host'],
    user=config['MySQL_config']['user'],
    password=config['MySQL_config']['password'],
    db=config['MySQL_config']['database'],
    cursorclass=pymysql.cursors.DictCursor
)

@app.route("/")
def index():
    # Execute a SELECT statement
    with connection.cursor() as cursor:
        sql = "select company.company_id, name, symbol, info_url  from company inner join ticker on company.company_id = ticker.company_id;"
        cursor.execute(sql)
        result = cursor.fetchall()
    return render_template('dashboard.html', data=result)

@app.route('/ticker/<symbol>')
def ticket(symbol): 
    symbol = symbol.strip()
    interval = 'day'  # The interval of the chart data (day, minute, etc.)
    limit = 30  # The number of data points to retrieve
    end_date = date.today().strftime('%Y-%m-%d')  # Today's date in the required format

    # Make the API request
    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/{interval}/2022-01-01/{end_date}?limit={limit}&apiKey={api_key}'
    response = requests.get(url)
    print( response.status_code )

    # Extract the data from the API response
    data = response.json()['results']

    # Extract the timestamps and closing prices from the data
    timestamps = [datapoint['t'] for datapoint in data]
    prices = [datapoint['c'] for datapoint in data]

    # Convert the timestamps to datetime objects
    dates = [datetime.fromtimestamp(timestamp / 1000) for timestamp in timestamps]

    # Create a Plotly line chart
    fig = go.Figure(data=go.Scatter(x=dates, y=prices))
    fig.update_layout(title=symbol, xaxis_title='Date', yaxis_title='Closing Price')

    # Format the date labels as desired
    date_format = '%m/%d/%Y'
    fig.update_layout(xaxis_tickformat=date_format)

    # Convert the chart to JSON format and pass it to the template
    chart_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # generate buy/sell recommendations using tradingview ta
    # tv = TA_Handler(
    # symbol=symbol,
    # screener="america",
    # exchange="NASDAQ",
    # interval=Interval.INTERVAL_5_MINUTES
    # )

    # recommendation = tv.get_analysis().summary['RECOMMENDATION'].replace('_',' ')
    # indicators = tv.get_indicators()

    # # relevant tech analysis
    # #rsi = indicators['RSI']
    # #stoch.k = indicators['Stoch.K']
    # #stock.d = indicators['Stoch.D']
    

    # calculate ema crossover
    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/2023-01-01/{end_date}?limit=30&apiKey={api_key}' 

    response = requests.get( url )
    data = response.json()['results']

    # Convert response to pandas dataframe and set timestamp as index
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
    df.set_index("timestamp", inplace=True)

    # Calculate 13 and 48 EMA
    df["ema13"] = df["c"].ewm(span=13).mean()
    df["ema48"] = df["c"].ewm(span=48).mean()

    # Check for crossover
    recommendation = ''
    last_ema13 = df["ema13"].iloc[-1]
    last_ema48 = df["ema48"].iloc[-1]
    if last_ema13 > last_ema48:
        recommendation = "Bullish crossover!, BUY"
    elif last_ema13 < last_ema48:
        recommendation = "Bearish crossover!, SELL"
    else:
         recommendation = "No crossover."

    color = ''
    if 'SELL' in recommendation:
        color = 'red'
    else:
        color = 'green'

    
    # fetch news
    sql = "select company.company_id, article, article_date, article_link  from company inner join news on company.company_id = news.company_id;"


    # Render the template and pass the chart data to it
    return render_template('ticker.html', chart_data=chart_data, recommendation=recommendation, color=color )


#@app.errorhandler(Exception)
def error(e):
    return render_template('error.html', error=e)


if __name__ == '__main__':
    app.run(debug=True)
