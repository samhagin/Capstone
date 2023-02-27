# Capstone
This is a default database capstone project that demostrates various uses of SQL. The app is a stock screener built with Flask that connects to a MySQL backend. This app can be accessed by going to http://stockscreener.online or http://165.227.201.84. If you wish to set this up locally or own your own server. Follow the instructions below:

# Requirements
Python 3.8 and MySQL 8 ( this app may however work with earlier version of MySQL without issues )

# Python packages required
- Flask
- BeautifulSoup
- requests
- pymysql 
- pandas
- textblob 

you can also run `pip install -r requirements.txt` to install these packages. 

# Deployment
To deploy the application, ensure you have MySQL running, then modify dbconnect.py and config.ini to include your database connection details and API key from Polygon.io ( used to fetch stock data )


## Database Setup
- create the MySQL database

```
mysql> create database capstone
``` 

- Import the database schema

`mysql capstone < database.sql` 

## Import Data
- run `python3.8 setup.py`. This script imports the initial data ( list of stocks from S&P 500, company meta data, news etc ) into the database. 

## Add MySQL views, triggers and stored procedures

```
mysql> create view ticker_list as select company.company_id, name, symbol, info_url  from company inner join ticker on company.company_id = ticker.company_id;
``` 


## Run the application
`python3.8 app.py` 

## You can access the application by going to

`127.0.01:5000` if being accessed locally or substitue `127.0.0.1` with the IP of the server you're running this on


