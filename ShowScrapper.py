import datetime
import requests
import logging
import util

from mysql.connector import Error
from mysql.connector import IntegrityError

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

class ShowScrapper:
    options=Options()
    options.headless = True
    driver = None
    logging.basicConfig(filename='scrapper.log',filemode='a', format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    explore_link='https://in.bookmyshow.com/explore/movies-'

    def get_analytics_for_movie_with_options(self,category_count,movie_link,dist_id,movie_id):
        if(category_count==0):
            return
        else:
            self.driver.get(movie_link)
            buttons=self.driver.find_elements(by=By.ID,value="page-cta-container")
            book_ticket=buttons[0]
            if(book_ticket is None):
                logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s',movie_link)
                return
            try:
                util.click(self.driver,book_ticket)
            except:
                logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK %s',movie_link)
                return
            categories=self.driver.find_elements(by=By.CLASS_NAME,value='sc-vhz3gb-3.bvxsIo')
            try:
                util.click(self.driver,categories[category_count-1])
            except:
                logging.warning('CANNOT CLICK CATEGORY FOR LINK - %s CATEGORY -%d',movie_link,category_count)
                return
            try:
                WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'showtime-pill')))
            except TimeoutException:
                logging.warning("Loading Time Exceeded for movie link : %s",movie_link)
                return
            soup=BeautifulSoup(self.driver.page_source,features="lxml")
            self.scrap_show_info(soup,dist_id,movie_id)
            self.get_analytics_for_movie_with_options(category_count-1,movie_link,dist_id,movie_id)

    def get_analytics_for_movie_without_options(self,movie_link,dist_id,movie_id):
        self.driver.get(movie_link)
        buttons=self.driver.find_elements(by=By.ID,value="page-cta-container")
        book_ticket=buttons[0]
        if(book_ticket is None):
            logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s @District : %d',movie_link,dist_id)
            return
        try:
            util.click(self.driver,book_ticket)
        except:
            logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK : %s @District : %d',movie_link,dist_id)
            return
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'showtime-pill')))
        except TimeoutException:
            logging.warning("Loading Time Exceeded for movie link : %s",movie_link)
        soup=BeautifulSoup(self.driver.page_source,features="lxml")
        self.scrap_show_info(soup,dist_id,movie_id)

    def scrap_show_info(self,soup,dist_id,movie_id):
        show_times=soup.find_all("a",{"class":"showtime-pill"})
        
        connection = util.get_connection()
        
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
                if(response.status_code!=200):
                    logging.warning("API CALL FAILED. SKIPPING THE SHOW : %s %s %s",movie_id,theatre_id,show_id)
                    continue
                query="insert into shows(dist_id,movie_id,theatre_id,show_id,cut_off_time,json_data) values({},\'{}\',\'{}\',\'{}\',\'{}\',\'{}\');".format(dist_id,movie_id,theatre_id,show_id,cut_off_time,repr(response.text)[1:-1])
                try:
                    cursor.execute(query)
                    logging.warning("INSERTING NEW SHOW %s %s %s",movie_id,theatre_id,show_id)
                except Error:
                    logging.warning("SHOW ALREADY PRESENT %s %s %s",movie_id,theatre_id,show_id)
                    query="update shows set json_data=\'{}\' where movie_id=\'{}\' and show_id=\'{}\' and theatre_id=\'{}\';".format(repr(response.text)[1:-1],movie_id,show_id,theatre_id)
                    logging.warning("UPDATING SHOW %s %s %s",movie_id,theatre_id,show_id)
                    try:
                        cursor.execute(query)
                    except:
                        logging.warning("SHOW UPDATION IN DB FAILED %s %s %s",movie_id,theatre_id,show_id)
        connection.commit()
        connection.close()
    
    def show_scrapper(self,territory_id):
        try:
            self.driver=webdriver.Firefox(options=self.options)
            now = datetime.datetime.now()
            logging.warning("SHOW SCRAPPING JOB INITIATED")
            connection = util.get_connection()
            cursor = connection.cursor(dictionary=True)
            query="select * from districts where territory_id={}".format(territory_id)
            cursor.execute(query)
            districts=cursor.fetchall()

            for row in districts:
                dist_id=row['district_id']
                self.driver.get(self.explore_link+row['link'])
                soup=BeautifulSoup(self.driver.page_source,features="lxml")
                has_movies=soup.find('div',text='Oops, there are no cinemas near you.')
                if has_movies is not None:
                    logging.warning("DISTRICT %s HAS NO MOVIES",row['dist_name'])
                    continue
                else:
                    logging.warning("SCRAPPING SHOWS IN DISTRICT : %s",row['dist_name'])
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
                    self.driver.get(link)
                    buttons=self.driver.find_elements(by=By.ID,value="page-cta-container")
                    book_ticket=None
                    try:
                        book_ticket=buttons[0]
                    except:
                        logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s',link)
                        continue
                    if(book_ticket is None):
                        logging.warning('BOOK TICKET BUTTON NOT FOUND FOR LINK : %s',link)
                        continue
                    try:
                        util.click(self.driver,book_ticket)
                    except:
                        logging.exception('CANNOT CLICK BOOK TICKET BUTTON FOR LINK %s',link)
                        continue
                    categories=self.driver.find_elements(by=By.CLASS_NAME,value='sc-vhz3gb-3.bvxsIo')
                    has_multiple_categories=True if len(categories)>0 else False
            
                    if has_multiple_categories:
                        logging.warning('MOVIE %s HAS MULTIPLE OPTIONS IN DISTRICT %s',movie_name,row['dist_name'])
                        self.get_analytics_for_movie_with_options(len(categories),link,dist_id,movie_id)
                    else:
                        self.get_analytics_for_movie_without_options(link,dist_id,movie_id)
        except:
            logging.exception('SCRAPPER FAILED DUE TO UNEXPECTED EXCEPTION')
        finally:
            connection.commit()
            connection.close()
            self.driver.close()
            now = datetime.datetime.now()
            logging.warning("SHOW SCRAPPING JOB ENDED")

