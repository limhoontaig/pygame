from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class craigslist_crawler(object):
    def __init__(self, query, max_price):
        self.max_price = max_price
        self.query = query
        self.url = f"https://seoul.craigslist.org/search/sss?query={query}&max_price={max_price}"
        self.driver = webdriver.Chrome("C:\IDE\chromedriver_win32\chromedriver.exe")
        self.delay = 5

    def load_page(self):
        driver = self.driver
        driver.get(self.url)
        all_data = driver.find_elements_by_class_name('result-row')
        for data in all_data:
            print(data.text) # price, title, date - text


# seoul.craigslist.org/search/sss?query=cup
# url =f"https://seoul.craigslist.org/search/sss?query={query}&max_price={max_price}"

query = 'iphone'
max_price = 1750
crawler = craigslist_crawler(query, max_price)
crawler.load_page()