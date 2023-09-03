import csv
import time

from slugify import slugify

from selenium import webdriver
from selenium.webdriver.common.by import By


class CoinMarketCap:
    def __init__(self, url):
        self.url = url
        self.driver = webdriver.Firefox()

    def get_tops(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(5)
        page_height = self.driver.execute_script('return document.body.scrollHeight')

        for scroll_height in range(0, page_height, 50):
            self.driver.execute_script(f'window.scrollTo(0, {scroll_height});')
            time.sleep(0.2)

        _coins = self.driver.find_elements(by=By.XPATH, value='//table/tbody/tr')
        coins = []
        for coin in _coins:
            cols = coin.find_elements(by=By.XPATH, value='.//td')
            coins.append(
                {
                    'Rank': cols[0].text,
                    'Name': cols[1].text,
                    'Symbol': cols[2].text,
                    'MainLink': f'https://coinmarketcap.com/currencies/{slugify(cols[1].text)}/',
                    'HistoricalLink': f'https://coinmarketcap.com/currencies/{slugify(cols[1].text)}/historical-data/',
                }
            )
        return coins

    @staticmethod
    def export_to_csv(filename: str, data: list, keys: list):
        with open(filename, 'w', newline='') as file:
            csv_writer = csv.DictWriter(file, fieldnames=keys)
            csv_writer.writeheader()
            csv_writer.writerows(data)

    def close(self):
        self.driver.close()
