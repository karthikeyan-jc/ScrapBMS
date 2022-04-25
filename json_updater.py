import datetime
import logging
from debugpy import connect
import util
import requests
import json

logging.basicConfig(filename='scrapper.log',filemode='a', format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')

def update_json():
    try:
        logging.warning('JSON UPDATER JOB INITIATED')
        now=datetime.datetime.now()
        three_hrs_back=now-datetime.timedelta(hours=3)
        time_upperbound=datetime.datetime.strftime(now,'%Y%m%d%H%M')

        if(now.day!=three_hrs_back.day):
            three_hrs_back=datetime.datetime(now.year,now.month,now.day,0,0,1)
        time_lowerbound=datetime.datetime.strftime(three_hrs_back,'%Y%m%d%H%M')

        query = "select * from shows where cut_off_time>\'{}\' and cut_off_time<\'{}\'".format(time_lowerbound,time_upperbound)

        connection=util.get_connection()
        cursor=connection.cursor(dictionary=True)
        cursor.execute(query)
        resultset=cursor.fetchall()

        for row in resultset:
            try:
                movie_id=row['movie_id']
                theatre_id=row['theatre_id']
                show_id=row['show_id']

                api_request = "https://in.bookmyshow.com/serv/getData?cmd=GETSHOWINFOJSON&vid={}&ssid={}&format=json".format(theatre_id,show_id)
                response=requests.get(api_request)
                if(response.status_code!=200):
                    continue
                existing_json=json.loads(row['json_data'])
                new_json=json.loads(response.text)
                
                if(len(existing_json['BookMyShow']['arrShowInfo'])==len(new_json['BookMyShow']['arrShowInfo'])):
                    query="update shows set json_data=\'{}\' where movie_id=\'{}\' and show_id=\'{}\' and theatre_id=\'{}\';".format(repr(response.text)[1:-1],movie_id,show_id,theatre_id)
                    cursor.execute(query)
                    connection.commit()
                else:
                    logging.warning("FAILED TO UPDATE JSON FOR %s %s %s",movie_id,theatre_id,show_id)
            except:
                continue
        
    except:
        logging.exception('JSON UPDATER FAILED')
    finally:
        logging.warning('JSON UPDATER JOB FINISHED')
        connection.commit()
        connection.close()
