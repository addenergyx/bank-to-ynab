# -*- coding: utf-8 -*-
"""
Created on Wed May 27 09:26:46 2020

@author: david
"""

from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from random import randrange

load_dotenv(verbose=True, override=True)

def get_driver(headless=False, proxy=False):
    
    options = Options()
    ua = UserAgent()
    userAgent = ua.random

    options.add_argument('user-agent={}'.format(userAgent))
    
    ## Headless browser - doesn't pop up
    ## A headless browser is a web browser without a graphical user interface.
    #options.add_argument("--headless") 
    if headless:    
        options.add_argument('--headless')
        
    # Full screen
    options.add_argument("--start-maximized")

    # Proxy to avoid 403 forbidden error
    # if proxy:
    #     prox = proxies[randrange(len(proxies))]
    #     print(prox)
    #     print('--------------------------------')
    #     options.add_argument('--proxy-server={}'.format(prox))

    WORKING_ENV = os.getenv('WORKING_ENV', 'development')
        
    if WORKING_ENV == 'development':
        return webdriver.Chrome(ChromeDriverManager().install(), options=options) # automatically use the correct chromedriver by using the webdrive-manager
    else:
        import sys
        sys.path.append(os.path.abspath("/home/pi/.local/lib/python3.7/site-packages/selenium/__init__.py"))
        sys.path.append(os.path.abspath("/usr/local/lib/python3.7/dist-packages/fake_useragent/__init__.py"))
        
        options.add_argument("--no-sandbox") #https://stackoverflow.com/questions/22424737/unknown-error-chrome-failed-to-start-exited-abnormally
        
        # https://ivanderevianko.com/2020/01/selenium-chromedriver-for-raspberrypi
        # https://www.reddit.com/r/selenium/comments/7341wt/success_how_to_run_selenium_chrome_webdriver_on/
        # https://askubuntu.com/questions/1090142/cronjob-unable-to-find-module-pydub
        # https://stackoverflow.com/questions/23908319/run-selenium-with-crontab-python
        return webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options) 

# driver = get_driver()
# driver.get("https://sslproxies.org/")
# driver.execute_script("return arguments[0].scrollIntoView(true);", WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//th[contains(., 'IP Address')]"))))
# ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 1]")))]
# ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 2]")))]
# driver.quit()
# proxies = [ips[i]+':'+ports[i] for i in range(0, len(ips))]

# def get_proxies():
    
#     driver = get_driver()
#    driver.get("https://sslproxies.org/")
#     driver.execute_script("return arguments[0].scrollIntoView(true);", WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//th[contains(., 'IP Address')]"))))
#     ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 1]")))]
#     ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 2]")))]
#     driver.quit()
    
#     proxies = [ips[i]+':'+ports[i] for i in range(0, len(ips))]
     
#     proxy = proxies[randrange(len(proxies))]
    
#     # proxies = s)
#     []
#     # for i in range(0, len(ips)):
#     #     proxies.append(ips[i]+':'+ports[i])
#     # print(proxie
#     return proxy

# driver = get_driver()
# driver.implicitly_wait(20)
def getPremarketChange(ticker, driver):

    #driver = get_driver(headless=True)
    #ticker = 'TSLA'
    
    #driver.implicitly_wait(20)        
    
    url = "https://www.webull.com/quote/nasdaq-" + ticker.lower()
    
    driver.get(url)
    
    price = driver.find_element_by_xpath("/html/body/div[1]/section/div[1]/div/div[2]/div[1]/div[3]/div[2]/div[2]/div/span").text
    
    # driver.close()
    # driver.quit()
    
    price = float(price.split()[0])
    
    # Using webull instead of nasdaq as nasdaq is slow
    #url = "https://www.nasdaq.com/symbol/" + ticker + "/premarket"
    #price = driver.find_element_by_xpath("/html/body/div[2]/div/main/div[2]/div[3]/section/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/div[2]/span[1]/span[2]").text
    #price = float(price[1:]) # strip $
    print(f'{ticker}: {price}')
    return price

# start = time.time()
# for ticker in ['tsla','aapl','fb']:
#     getPremarketChange(ticker, driver)
# end = time.time()
# print(end - start)
# driver.close()
# driver.quit()
    
# import pandas as pd
# from sqlalchemy import create_engine

# db_URI = os.getenv('AWS_DATABASE_URL')
# engine = create_engine(db_URI)
# holdings = pd.read_sql_table("portfolio", con=engine, index_col='index')

# ll = holdings['Ticker'].drop_duplicates()

# import time
# start = time.time()
# for ticker in ['tsla','aapl','fb']:
#     getPremarketChange(ticker)
# end = time.time()
# print(end - start)

# inside: 13.626956939697266
# outside: 3.4367830753326416

def get_tesco_vouchers():
    
    count = 0
    max_tries = 3
    
    try:
        driver = webdriver.Chrome('./chromedriver')
                
        driver.get('https://secure.tesco.com/account/en-GB/login?from=http://secure.tesco.com/clubcard/')
        
        ## Login
        driver.find_element_by_xpath('//*[@id="username"]').send_keys(os.getenv('MY_EMAIL'))
        driver.find_element_by_id('password').send_keys(os.getenv('TESCO_PASS'))
        
        ## Click random place to not appear like a robot
        driver.find_element_by_class_name('ui-component__form-header').click()
        
        #time.sleep(5) #Ensures page load before continuing
        driver.find_element_by_xpath('//*[@id="sign-in-form"]/button').click()
        
        driver.get('https://secure.tesco.com/clubcard/MyAccount/Home/Home')
        
        time.sleep(5) #Ensures page load before continuing
        tesco_vouchers = "£{}".format(driver.find_element_by_id('vouchersValue').text)
    
    except NoSuchElementException as e:
        
        count = count + 1
        
        if count == max_tries:
            print (e) 
        else:
            print('error')
            time.sleep(10)
            get_tesco_vouchers()
    print ('quit')    
    driver.quit()
    
    return tesco_vouchers

def get_iceland_balance():
    
    count = 0
    max_tries = 3
    
    try:

        driver = get_driver()
        driver.get('https://mybonuscard.iceland.co.uk/')
        driver.find_element_by_id('cardNumber').send_keys(os.getenv('ICELAND_USER'))
        driver.find_element_by_name('Submit').click()
        driver.find_element_by_id('password').send_keys(os.getenv('ICELAND_PASS'))
        driver.find_element_by_name('Login').click()
        iceland_balance = driver.find_element_by_xpath('//*[@id="cardBalanceAmount"]/p/span').text
    
    except NoSuchElementException as e:
        
        count = count + 1
        
        if count == max_tries:
            print (e) 
        else:
            time.sleep(10)
            get_iceland_balance()
        
    driver.quit()
    
    return iceland_balance

# Don't need this anymore, can get dates from iexfinance module
def get_div_details():
   
    # count = 0
    # max_tries = 3
    
    try:

        driver = get_driver()
        
        dividend_dict = {}
        
        symbols = ['AAPL','O','LTC']
    
        for symbol in symbols:
            driver = webdriver.Chrome('./chromedriver')

            driver.get(f'https://www.nasdaq.com/market-activity/stocks/{symbol}/dividend-history')
        
            time.sleep(5)

            ## SITE DOESN'T USE ID's
            ex_div_date = driver.find_element_by_xpath('/html/body/div[1]/div/main/div/div[4]/div[1]/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/th').text
            pay_date = driver.find_element_by_xpath('/html/body/div[1]/div/main/div/div[4]/div[1]/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[5]').text

            if datetime.strptime(ex_div_date, '%m/%d/%Y').date() < datetime.today().date() and datetime.strptime(pay_date, '%m/%d/%Y').date() < datetime.today().date():
                print('Missed ex dividend and payout date so wont add to calendar')
                continue

            div_yield = driver.find_element_by_xpath ('/html/body/div[1]/div/main/div/div[4]/div[1]/div/div[2]/ul/li[2]/span[2]/span').text
            annual_dividend = driver.find_element_by_xpath('/html/body/div[1]/div/main/div/div[4]/div[1]/div/div[2]/ul/li[3]/span[2]/span').text
            payout_ratio = driver.find_element_by_xpath('/html/body/div[1]/div/main/div/div[4]/div[1]/div/div[2]/ul/li[4]/span[2]/span').text
            
            ticker = yf.Ticker(symbol)
            
            # msft.get_dividends()
            # msft.get_calendar()
            name = ticker.info['longName']
    
            dividend_dict[symbol] = {
                                       'EX-DIVIDEND DATE':ex_div_date,
                                       'DIVIDEND YIELD':div_yield,
                                       'PAYOUT RATIO':payout_ratio,
                                       'ANNUAL DIVIDEND':annual_dividend,
                                       'PAYMENT DATE':pay_date,
                                       'COMPANY NAME':name
                                      }
            
            ## Dividend payouts from Trading 212 usually take up to 3 working days after the official payment date.
            
    except NoSuchElementException as e:
        
        # count = count + 1
        
        # if count == max_tries:
        print("%s\n" % e)
        # else:
        #     time.sleep(10)
        #     get_div_details()
        
    driver.quit()
    
    return dividend_dict



