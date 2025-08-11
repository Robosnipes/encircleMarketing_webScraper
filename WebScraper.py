#Web Scraper for www.National.co.uk with lightweight command-line interface
#Programmed by Lucas Chan

from bs4 import BeautifulSoup
import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime
import re
import sys

#homepage
base_url = 'https://www.national.co.uk/'
test_url = base_url + '/tyres-search/205-55-16?pc=S434JN'

#database (SQLite)
conn = sqlite3.connect('tyres.db', timeout=10)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS tyres ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    pattern TEXT NOT NULL,
    grip TEXT NOT NULL,
    fuel_efficiency TEXT NOT NULL,
    seasonality TEXT,
    price REAL NOT NULL,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    UNIQUE(brand, pattern, seasonality, grip, fuel_efficiency, price)
    )
           ''')

#input loop
def param_input():
    print("www.national.co.uk | Web Scraper by Lucas Chan")
    
    response_valid = False
    while response_valid != True:
        try:
            exit_input = int(input("1 to Continue\n0 to Exit\n> "))
            if exit_input == 0:
                print("--Exiting.--")
                
                #close database connection
                c.close()
                conn.close()
                
                #exit program
                sys.exit()
                
            
            #numeric inputs for search query
            width = int(input("Width: "))
            aspect_ratio = int(input("Aspect ratio: "))
            rim_size = int(input("Rim size: "))
            
            #clean postcode input
            postcode = input("Postcode: ").strip().upper().replace(" ", "")
            
            #REGEX obtained from 'Bulk Data Transfer: Additional Validation For CAS Upload' at GOV.UK
            postcode_expression = re.compile('^([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([AZa-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9]?[A-Za-z]))))[0-9][A-Za-z]{2})$')
            
            #postcode validation
            if not postcode_expression.match(postcode):
                print("--Invalid postcode format.--\n")
                continue
            
            #success, construct request URL    
            response_valid = True
            url = base_url + "/tyres-search/" + str(width) + "-" + str(aspect_ratio) + "-" + str(rim_size) + "?pc=" + postcode
            
            scrape_page(url)
            
        except ValueError:
            print("--Width, Aspect Ratio and Rim Size must be integer values.--")
        
            
#scrape function
def scrape_page(url):
    #ethical considerations
    time.sleep(2)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0'
    }
    
    #setup scraper
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    tyre_elements = soup.find_all("div", {'class': ['tyreDisplay']})
    
    #exit if no tyre results
    if not tyre_elements:
        print("\n--No results found.--")
        param_input()
    
    #extract tyre data
    for tyre in tyre_elements:
        #attributes = tyre.attrs
        
        grip = tyre['data-grip']
        fuel_efficiency = tyre['data-fuel']
        price = tyre['data-price']
        brand = tyre['data-brand']
        seasonality = tyre['data-tyre-season']
        
        pattern_link = tyre.find('a', class_='pattern_link')
        pattern = pattern_link.text 
        
        #insert into database
        c.execute('''INSERT OR IGNORE INTO tyres
                  (brand, pattern, grip, fuel_efficiency, seasonality, price, date, source)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                  ''',
                  (brand, pattern, grip, fuel_efficiency, seasonality, price, datetime.now().isoformat(), url)
                  )
        
    #save database changes    
    conn.commit()
    
    #output database table
    c.execute("SELECT * FROM tyres")
    rows = c.fetchall()

    for row in rows:
        print("\n",row)

    #export as csv
    df = pd.read_sql_query("SELECT * FROM tyres", conn)
    df.to_csv(r'tyres.csv', index=False)
    
    
    #close database connection
    c.close()
    conn.close()


#testing (uncomment line below)
#scrape_page(test_url)

param_input()

