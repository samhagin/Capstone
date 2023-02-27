import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="capstone"
)

mycursor = mydb.cursor( buffered=True ) 
