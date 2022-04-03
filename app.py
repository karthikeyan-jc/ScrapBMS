from flask import Flask
from mysql.connector import Error
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import theatre_scrapper
import show_scrapper

def server_shutdown():
    print('BYE BYE')
    sched.shutdown()

sched = BackgroundScheduler(daemon=True)
sched.add_job(theatre_scrapper.theatre_scrapper,'interval',seconds=5)
sched.add_job(show_scrapper.show_scrapper,'interval',seconds=7)
sched.start()
atexit.register(server_shutdown)

app = Flask(__name__)

if __name__ == "__main__":
    app.run()