from bs4 import BeautifulSoup
import requests, time
from dbconnect import * 
import time, configparser

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['Polygon']['api_key']

# fetch list of stocks
url = 'https://www.slickcharts.com/sp500'

headers = { "User-Agent": "Mozilla"}
r = requests.get( url, headers=headers )

# Check if the request was successful
if r.status_code == 200:
    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the table in the HTML
    table = soup.find("table", {"class": "table-borderless"})

    # Extract the data from the table
    rows = table.find_all("tr")
    for row in rows:
       columns = row.find_all('td')

       if(columns != []):
          name = columns[1].text.strip()
          ticker = columns[2].text.strip().replace('.','-')
          info_url = 'https://finviz.com/quote.ashx?t={}&p=d'.format( ticker )
          print( name, '|', ticker, '|', info_url )
          
          # verify url 
          check = requests.get( info_url , headers=headers )
          if check.status_code == 200:
             # insert into database
             sql = "INSERT INTO company (name, info_url ) VALUES (%s, %s)"
             val = ( name, info_url )
             mycursor.execute(sql, val)
             print( mycursor.rowcount )       
             mydb.commit()
             time.sleep(1)

else:
    print("Failed to scrape data. Response code:", r.status_code)


# company meta
sql = "select * from company"
mycursor.execute( sql )
myresult = mycursor.fetchall()

headers = { "User-Agent": "Mozilla" }
for i in myresult:
   url = i[-1]
   company_id = i[0]
   r = requests.get( url , headers=headers )
   soup = BeautifulSoup( r.text, "html.parser" )
   ticker = soup.find(id='ticker').text
   about = soup.find(class_='fullview-profile').text
   print( company_id, ticker, about )

   # insert data into company_meta table 
   sql = "INSERT INTO company_meta ( company_id, about ) values ( %s,%s )"
   val = ( company_id, about )
   mycursor.execute( sql, val )
    
   # insert data into ticker table 
   sql = "INSERT INTO ticker ( company_id, symbol ) values ( %s,%s )"
   val = ( company_id, ticker )
   mycursor.execute( sql, val )
   
   mydb.commit()
   time.sleep( 1 )

# news
mycursor.reset()
sql = "SELECT * from company"
mycursor.execute( sql )
myresult = mycursor.fetchall()

for i in myresult:
    company_id = i[0]
    company = i[1]
    info_url = i[-1]
    r = requests.get( info_url, headers=headers )
    soup = BeautifulSoup( r.text, "html.parser" )
    date = soup.find(class_='fullview-news-outer').find('td').text
    news_link = soup.find(class_='news-link-left').a['href']
    news_text = soup.find(class_='news-link-left').text
    print( date, news_link, news_text )
    sql = "INSERT INTO news ( company_id, article,article_date, article_link ) values ( %s, %s, %s, %s )"
    val = ( company_id, news_text, date, news_link )
    mycursor.execute( sql, val )
    mydb.commit() 

# fetch stock prices from API 
sql = "select company.company_id, name, symbol, info_url  from company inner join ticker on company.company_id = ticker.company_id"
mycursor.execute( sql )
myresult = mycursor.fetchall() 

for i in myresult:
   ticker = i[2]
   ticker = ticker.replace('-','.')
   url = f'https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={api_key}'
   try:
      r = requests.get( url )
      prevDay = r.json()['ticker']['prevDay']['c']
      day = r.json()['ticker']['day']['c']
      print( prevDay, day )
      sql = "update ticker set prevDay=%s, day=%s where symbol=%s"
      val = ( prevDay, day, ticker )
      mycursor.execute( sql, val )
      mydb.commit()
   except Exception as e:
     print( e )
 
