from ShowScrapper import ShowScrapper
from flask import Flask
from mysql.connector import Error
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import theatre_scrapper
import json_updater
import threading

def server_shutdown():
    print('BYE BYE')
    sched.shutdown()

def initiate_showscrapping_threads():
    scrapper1=ShowScrapper()
    scrapper2=ShowScrapper()
    scrapper3=ShowScrapper()
    thread1=threading.Thread(target=scrapper1.show_scrapper,args=[1])
    thread2=threading.Thread(target=scrapper2.show_scrapper,args=[2])
    thread3=threading.Thread(target=scrapper3.show_scrapper,args=[3])

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

sched = BackgroundScheduler(daemon=True)
sched.add_job(theatre_scrapper.theatre_scrapper,'interval',minutes=720)
sched.add_job(initiate_showscrapping_threads,'interval',minutes=15)
sched.add_job(json_updater.update_json,'interval',minutes=30)
sched.start()
atexit.register(server_shutdown)

app = Flask(__name__)

if __name__ == "__main__":
    app.run()