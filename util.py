from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import configparser
import mysql.connector

#UTILITY METHOD FOR CLICKING ELEMENTS AS THERE ARE POSSIBILITES OF OTHER ELEMENTS OBSCURING THE INTENDED ELEMENT.
def click(driver,element):
    try:
        cancel=driver.find_element(by=By.ID,value="wzrk-cancel")
        cancel.click()
    except NoSuchElementException:
        pass
    finally:
        element.click()

def get_connection():
    config= configparser.ConfigParser()
    config.read('config.ini')
    config_info=config['mysqlDB']

    connection = mysql.connector.connect(host=config_info['host'],
                                         database=config_info['database'],
                                         user=config_info['user'],
                                         password=config_info['password'])
    return connection