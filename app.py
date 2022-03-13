from curses import tparm
from flask import Flask
from flask import request
import mysql.connector
import requests
from mysql.connector import Error
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/moviecollection',methods=['GET'])
def movie_collection():
    movie_id = request.args.get('id')
    connection = mysql.connector.connect(host='localhost',
                                         database='scrapbms',
                                         user='karthi',
                                         password='password')
    query="select * from shows where shows.movie_id= \'{}\'".format(movie_id)
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    shows=cursor.fetchall()
    collection=0
    total_seats=0
    seats_sold=0
    for row in shows:
        row_dict=json.loads(row['json_data'])
        ticket_categories=(row_dict['BookMyShow']['arrShowInfo'])
        for tc in ticket_categories:
            collection+=int(tc['Price'])*(int(tc['TotalSeats'])-int(tc['AvailableSeats']))
            total_seats+=int(tc['AvailableSeats'])
            seats_sold+=(int(tc['TotalSeats'])-int(tc['AvailableSeats']))
    response={}
    response['Total Seats']=str(total_seats)
    response['Seats Sold']=str(seats_sold)
    response['Revenue']=str(collection)+' Rs'
    connection.close()
    return response

    