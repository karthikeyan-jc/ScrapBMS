from flask import Flask
from flask import request
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from flask_apscheduler import APScheduler
import theatre_scrapper
import show_scrapper

app = Flask(__name__)

if (__name__ == "__main__"):
    scheduler = APScheduler()
    scheduler.add_job(func=theatre_scrapper.theatre_scrapper, trigger='interval', id='theatre_scrapper',minutes=2)
    scheduler.add_job(func=show_scrapper.show_scrapper, trigger='interval', id='show_scrapper',minutes=2)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    app.run(port = 8000)


@app.route('/moviecollection',methods=['GET'])
def movie_collection():
    return 'Contract not yet defined :)'

