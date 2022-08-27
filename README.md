# ScrapBMS
A Selenium driven, highly scalable bot that is capable of scraping the booking details of all movies available on Book My Show.

# Architecture
This is a flask application containing two selenium bots (TheatreScrapper and ShowScrapper) that run on periodic intervals using APScheuler. As the name suggests, ShowScrapper gets the booking details of all the movies currently available on BMS, whereas TheatreScrapper gets the details of all the theatres.
Apart from the two bots there is also another periodic job which updates the already scraped data so that the bookings happening between two ShowScrapper sessions won't be missed. 
# Installation
1. Before proceeding with the installation make sure you have a working confiuration of selenium and browser driver. This is highly dependent on machine and OS that you are working on. So please browse for the appropriate tutorial. Once you have successfully executed a test browser automation script, proceed with the rest of the steps.
2. Make a virtual environment and activate it.
3. Install the dependent libraries
```sh
   pip install -r requirements.txt
```
4. Refer the images 'DB Schema.png' and 'Data example.png' to set up the database and populate it
5. Run the application
```sh
   python app.py
```
