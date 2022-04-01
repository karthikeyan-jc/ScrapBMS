import datetime
import requests
import configparser
import logging
import util

import mysql.connector
from mysql.connector import Error
from mysql.connector import IntegrityError

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
options=Options()
options.headless = True
driver = None
logging.basicConfig(filename='scrapper.log',filemode='a', format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')
explore_link='https://in.bookmyshow.com/explore/movies-'

def get_analytics_for_movie_with_options(category_count,movie_link,dist_id,movie_id):
    if(category_count==0):
        return
    else:
        driver.get(movie_link)
        buttons=driver.find_elements(by=By.ID,value="page-cta-container")
        book_ticket=buttons[0]
        if(book_ticket is None):
            logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s',movie_link)
            return
        try:
            util.click(driver,book_ticket)
        except:
            logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK %s',movie_link)
            return
        categories=driver.find_elements(by=By.CLASS_NAME,value='sc-vhz3gb-3.bvxsIo')
        try:
            util.click(driver,categories[category_count-1])
        except:
            logging.warning('CANNOT CLICK CATEGORY FOR LINK - %s CATEGORY -%d',movie_link,category_count)
            return
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'showtime-pill')))
        except TimeoutException:
            logging.warning("Loading Time Exceeded for movie link : %s",movie_link)
            return
        soup=BeautifulSoup(driver.page_source,features="lxml")
        scrap_show_info(soup,dist_id,movie_id)
        get_analytics_for_movie_with_options(category_count-1,movie_link,dist_id,movie_id)

def get_analytics_for_movie_without_options(movie_link,dist_id,movie_id):
    driver.get(movie_link)
    buttons=driver.find_elements(by=By.ID,value="page-cta-container")
    book_ticket=buttons[0]
    if(book_ticket is None):
        logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s @District : %d',movie_link,dist_id)
        return
    try:
        util.click(driver,book_ticket)
    except:
        logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK : %s @District : %d',movie_link,dist_id)
        return
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'showtime-pill')))
    except TimeoutException:
        logging.warning("Loading Time Exceeded for movie link : %s",movie_link)
    soup=BeautifulSoup(driver.page_source,features="lxml")
    scrap_show_info(soup,dist_id,movie_id)

def get_connection():
    config= configparser.ConfigParser()
    config.read('config.ini')
    config_info=config['mysqlDB']

    connection = mysql.connector.connect(host=config_info['host'],
                                         database=config_info['database'],
                                         user=config_info['user'],
                                         password=config_info['password'])
    return connection

def scrap_show_info(soup,dist_id,movie_id):
    show_times=soup.find_all("a",{"class":"showtime-pill"})
    
    connection = get_connection()
    
    cursor=connection.cursor(dictionary=True)
    for j in show_times:
            show_link=j.get("href")
            if(show_link is None):
                continue
            cut_off_time=j.get('data-cut-off-date-time')
            if(cut_off_time is None):
                continue
            now = datetime.datetime.now()
            now_str = now.strftime("%Y%m%d%H%M")
            if(now_str>cut_off_time):
                continue
            theatre_id=j.get('data-venue-code')
            show_id=j.get('data-session-id')
            api_request = "https://in.bookmyshow.com/serv/getData?cmd=GETSHOWINFOJSON&vid={}&ssid={}&format=json".format(theatre_id,show_id) 
            response=requests.get(api_request)
            query="insert into shows(dist_id,movie_id,theatre_id,show_id,cut_off_time,json_data) values({},\'{}\',\'{}\',\'{}\',\'{}\',\'{}\');".format(dist_id,movie_id,theatre_id,show_id,cut_off_time,response.text)
            try:
                cursor.execute(query)
                logging.warning("INSERTING NEW SHOW %s %s %s",movie_id,theatre_id,show_id)
            except Error:
                logging.warning("SHOW ALREADY PRESENT %s %s %s",movie_id,theatre_id,show_id)
                query="update shows set json_data=\'{}\' where movie_id=\'{}\' and show_id=\'{}\';".format(response.text,movie_id,show_id)
                logging.warning("UPDATING SHOW %s %s %s",movie_id,theatre_id,show_id)
                try:
                    cursor.execute(query)
                except:
                    logging.warning("SHOW UPDATION IN DB FAILED %s %s %s",movie_id,theatre_id,show_id)
    connection.commit()
    connection.close()

def show_scrapper():
    try:
        global driver
        driver=webdriver.Firefox(options=options)
        now = datetime.datetime.now()
        logging.warning("SHOW SCRAPPING JOB INITIATED")
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query="select * from districts"
        cursor.execute(query)
        districts=cursor.fetchall()

        for row in districts:
            dist_id=row['id']
            logging.warning("SCRAPPING SHOWS IN DISTRICT : %s",row['dist_name'])
            driver.get(explore_link+row['link'])
            soup=BeautifulSoup(driver.page_source,features="lxml")
            shows=soup.find_all("a", {"class": "sc-133848s-11 sc-1ljcxl3-1 eQiiBj"})
            for i in shows[1:]:
                link = i.get("href")
                movie_name=link.split('https://in.bookmyshow.com/',1)[1].split('/')[2]
                movie_id=link.split('https://in.bookmyshow.com/',1)[1].split('/')[3]
                query="insert into movies(movie_id,movie_name) values(\'{}\',\'{}\');".format(movie_id,movie_name)
                try:
                    logging.warning('INSERTING NEW MOVIE %s',movie_name)
                    cursor.execute(query)
                    connection.commit()
                except IntegrityError:
                    logging.warning("MOVIE %s ALREADY ADDED",movie_name)
                except Error:
                    logging.exception("DATABASE ERROR WHILE INSERTING MOVIE %s",movie_name)
                    continue
                driver.get(link)
                buttons=driver.find_elements(by=By.ID,value="page-cta-container")
                book_ticket=buttons[0]
                if(book_ticket is None):
                    logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s',link)
                    continue
                try:
                    util.click(driver,book_ticket)
                except:
                    logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK %s',link)
                    continue
                categories=driver.find_elements(by=By.CLASS_NAME,value='sc-vhz3gb-3.bvxsIo')
                has_multiple_categories=True if len(categories)>0 else False
        
                if has_multiple_categories:
                    logging.warning('MOVIE %s HAS MULTIPLE OPTIONS IN DISTRICT %s',movie_name,row['dist_name'])
                    get_analytics_for_movie_with_options(len(categories),link,dist_id,movie_id)
                else:
                    get_analytics_for_movie_without_options(link,dist_id,movie_id)
    except:
        logging.exception('SCRAPPER FAILED DUE TO UNEXPECTED EXCEPTION')
    finally:
        connection.commit()
        connection.close()
        driver.close()
        now = datetime.datetime.now()
        logging.warning("SHOW SCRAPPING JOB ENDED")