from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import configparser
app = Flask(__name__)

config = configparser.ConfigParser()
config.read('dbconfig.ini')

app.config['MYSQL_HOST'] = config['MySQL_config']['host']
app.config['MYSQL_USER'] = config['MySQL_config']['user']
app.config['MYSQL_PASSWORD'] = config['MySQL_config']['password']
app.config['MYSQL_DB'] = config['MySQL_config']['database']

mysql = MySQL(app)

@app.route("/")
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM company')
    companies = cursor.fetchall() 
    data = []
    for company in companies:
        data.append( company ) 
    return render_template("dashboard.html", data = data )

if __name__ == "__main__":
    app.run(debug=True)
