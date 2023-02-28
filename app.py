from flask import Flask, Response, render_template, request, redirect, url_for, session, flash
import pymysql
import configparser
import plotly.graph_objs as go
from datetime import datetime, date, timedelta
import base64, requests, json, plotly, re
from tradingview_ta import TA_Handler, Interval, Exchange
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from textblob import TextBlob

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config['Polygon']['api_key']

app = Flask(__name__)
app.secret_key = '2rzpXVhAidTwbMKM0yhTlciRmpBOiz9J'

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
    ticker = ''
    result = ''
    print( session, flush=True )
    with connection.cursor() as cursor:
        sql = "select * from ticker_list"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

    # check change in price
    # prevDay = day = ''
    # for i in result:
    #     ticker = i['symbol']
    #     print( ticker, flush=True )
    #     try:
    #       url = f'https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={api_key}'
    #       r = requests.get( url )
    #       # print( r.json(), flush=True )
    #       prevDay = r.json()['ticker']['prevDay']['c']
    #       day = r.json()['ticker']['day']['c']
    #       print( prevDay, day, flush=True )
    #     except:
    #         pass

    return render_template('index.html', data=result)

@app.route('/ticker/<symbol>')
def ticket(symbol): 
    symbol = symbol.strip()
    interval = 'day'  # The interval of the chart data (day, minute, etc.)
    limit = 30  # The number of data points to retrieve
    end_date = date.today().strftime('%Y-%m-%d')  # Today's date in the required format

    # fetch news
    company_id = ''
    sentiment = ''
    with connection.cursor() as cursor:
        sql = 'select * from ticker where symbol = %s'
        cursor.execute(sql, symbol )
        result = cursor.fetchone()
        company_id = result['company_id']

        sql = "select article, article_date, article_link from news where company_id = %s"
        cursor.execute( sql, company_id )
        result = cursor.fetchall()
        for i in result:
            url = i['article_link']
            response = requests.get( url )
            content = response.text 
            blob = TextBlob(content)
            sentiment = blob.sentiment.polarity

            if sentiment > 0:
               sentiment = 'Positive'
            elif sentiment < 0:
               sentiment = 'Negative'
            else:
               sentiment = 'Neutral'
        cursor.close()

    

    # calculate ema crossover
    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/2023-01-01/{end_date}?limit=30&apiKey={api_key}' 
    
    data = '' 
    recommendation = '' 
    color = '' 
    last_ema13 = ''
    last_ema48 = '' 
    ema_direction = ''
    try: 
        response = requests.get( url ) 
        if  response.status_code == 200: 
            data = response.json().get('results') 

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

    except KeyError as ke:
         data = 'Unable to fetch data for this ticker', ke
    print( recommendation, flush=True )

    
    # tradingview chart url
    exchange = 'NYSE'
    tv_url = f'https://www.tradingview.com/symbols/{exchange}-{symbol}/'
    r = requests.get( tv_url )
    if r.status_code != 200:
        exchange = 'NASDAQ'
        tv_url = f'https://www.tradingview.com/symbols/{exchange}-{symbol}/'

    
    # fetch company about text
    about = ''
    with connection.cursor() as cursor:
        sql = 'select about from company_meta where company_id = %s'
        cursor.execute(sql, company_id )
        about = cursor.fetchall()
        about = about[0]['about']
        cursor.close()


    # get RSI
    rsi = ''
    url = f'https://api.polygon.io/v1/indicators/rsi/{symbol}?timespan=minute&adjusted=true&window=14&series_type=close&order=desc&limit=1&apiKey={api_key}'
    r = requests.get( url )
    rsi = r.json()['results']['values'][0]['value'] 

    if 'SELL' in recommendation and int(rsi) > 70:
        color = 'red'
        ema_direction = recommendation = 'SELL'
    elif 'BUY' in recommendation and int(rsi) < 30:
        color = 'green'
        ema_direction = recommendation = 'BUY'
    else: 
        color = 'grey'
        ema_direction = recommendation = 'NEUTRAL'

    print( ema_direction, flush=True)

    #insert ema into database
    with connection.cursor() as cursor:
       cursor.execute('select * from ema_cross where company_id = %s', (company_id,))
       current_ema = cursor.fetchone()

       if current_ema == None: 
          sql = 'insert into ema_cross ( ema_direction, company_id ) values ( %s, %s )'
          val = ( ema_direction, company_id )
          cursor.execute(sql, val )
          connection.commit()
    cursor.close()

    # add RSI value to database
    with connection.cursor() as cursor:
        cursor.execute('select * from rsi where company_id = %s', (company_id,))
        current_ema = cursor.fetchone()
        sql = 'insert into rsi ( rsi_5, company_id ) values ( %s, %s )'
        val = ( rsi, company_id )
        cursor.execute(sql, val )
        connection.commit()
        cursor.close() 


    # check sentiment


    # Render the template and pass the chart data to it
    return render_template('ticker.html', sentiment=sentiment, recommendation=recommendation, color=color, data=result, ticker=symbol, tv_url=tv_url, exchange=exchange, last_ema13=round(last_ema13,2), last_ema48=round(last_ema48,2), rsi=round(rsi,2), about=about )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['logged_in']=True
            return redirect('/dashboard')
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, hashed_password))
        connection.commit()
        cursor.close()
        flash('Registration successful. Please login.')
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    try:
      if session['logged_in']==False:
         flash("You must be logged in to access this page")
         return redirect('/login')
      elif session['logged_in']==True: 
         return render_template('dashboard.html')
    except:
      return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#@app.errorhandler(Exception)
def error(e):
    return render_template('error.html', error=e)


if __name__ == '__main__':
     app.run(debug=True, port=5000, host='0.0.0.0')
