from mysql.connector import Error
from mysql.connector import IntegrityError

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

import logging
import datetime
import util

theatre_query_template="insert into theatres(dist_id,theatre_id,theatre_name) values({},\'{}\',\'{}\');"    
logging.basicConfig(filename='scrapper.log',filemode='a', format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')

def theatre_scrapper():
    now = datetime.datetime.now()
    
    options=Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    explore_link='https://in.bookmyshow.com/explore/home/'

    connection = util.get_connection()
    cursor = connection.cursor(dictionary=True)
    query="select * from districts"
    cursor.execute(query)
    districts=cursor.fetchall()

    try:
        logging.warning('THEATRE SCRAPPING STARTED')
        for row in districts:
            dist_id=row['district_id']
            logging.warning('SCRAPPING THEATRES IN %s',row['dist_name'])
            driver.get(explore_link+row['link'])
            element = driver.find_element(by=By.CLASS_NAME,value="sc-bZQynM.sc-dEoRIm.hSiMIq")
            util.click(driver,element)
            element = driver.find_element(by=By.CLASS_NAME,value="sc-cfWELz.dyuKpT")
            util.click(driver,element)
            theatres=driver.find_elements(by=By.CLASS_NAME,value="sc-lnrBVv.gpuQNF")
            new_theatres=driver.find_elements(by=By.CLASS_NAME,value="sc-hkbPbT.iIDrmE")
            theatres.extend(new_theatres)
    
            for theatre in theatres:
                theatre_details=theatre.get_property('href').split('https://in.bookmyshow.com/buytickets/',1)[1].split('/')
                theatre_id=theatre_details[1].split('-')[2]
                theatre_name=theatre.text
    
                query=theatre_query_template.format(dist_id,theatre_id,theatre_name)
                try:
                    cursor.execute(query)
                    logging.warning("NEW THEATRE ADDED %s",theatre_name)
                except IntegrityError:
                    logging.warning("THEATRE %s ALREADY PRESENT",theatre_name)
                    continue
                except Error:
                    logging.exception("DATABASE ERROR WHILE INSERTING THEATRE %s",theatre_name)
                    continue
    except:
        logging.exception("THEATRE SCRAPPING FAILED")
    finally:
        connection.commit()
        connection.close()
        driver.close()
        now = datetime.datetime.now()
        logging.warning('THEATRE SCRAPPING ENDED')