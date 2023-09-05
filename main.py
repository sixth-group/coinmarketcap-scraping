import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException, StaleElementReferenceException


class CoinMarketCap:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def get_tops(self, url='https://coinmarketcap.com/historical/20230825/'):
        self.driver.get(url)
        self.driver.implicitly_wait(5)
        page_height = self.driver.execute_script('return document.body.scrollHeight')

        for scroll_height in range(0, page_height, 50):
            self.driver.execute_script(f'window.scrollTo(0, {scroll_height});')
            time.sleep(0.1)

        _coins = self.driver.find_elements(by=By.XPATH, value='//table/tbody/tr')
        coins = []
        for coin in _coins:
            cols = coin.find_elements(by=By.XPATH, value='.//td')
            main_link = cols[1].find_element(by=By.XPATH, value='.//a').get_attribute('href')
            coins.append(
                {
                    'Rank': cols[0].text,
                    'Name': cols[1].text,
                    'Symbol': cols[2].text,
                    'MainLink': main_link,
                    'HistoricalLink': f'{main_link}historical-data/',
                }
            )
        return coins

    def get_history_of_coins(self, coins: list[dict]):
        for coin in coins:
            historical_page_url = coin['HistoricalLink']
            self.driver.get(historical_page_url)
            self.driver.implicitly_wait(5)
            self.driver.execute_script('window.scrollTo(0, 0);')

            self.driver.find_element(by=By.XPATH,
                                     value="//div[@data-role='btn-content']//*[name()='svg']"
                                           "/*[name()='use' and @href='#calendar']/parent::*/parent::*").click()
            self.driver.find_element(by=By.XPATH, value="//li[text()='Last 365 days']").click()
            self.driver.find_element(by=By.XPATH, value="//button[text()='Continue']").click()

            time.sleep(2)

            self.driver.find_element(by=By.XPATH, value="//div[contains(text(), 'Download CSV')]").click()

            time.sleep(2)

    def get_detail_of_coins(self, coins: list[dict]):
        without_tag_coins = []
        for coin in coins:
            self.driver.get(coin['MainLink'])
            self.driver.implicitly_wait(5)
            self.driver.execute_script('window.scrollTo(0, 0);')

            sidebar = self.driver.find_element(by=By.XPATH, value="//div[contains(@class, 'content_folded')]")

            github_url = None
            try:
                github_url = sidebar.find_element(by=By.XPATH,
                                                  value=".//span[text()='Official links']"
                                                        "//following::div[1]"
                                                        "//a[contains(text(), 'GitHub')]")
                github_url = github_url.get_attribute('href')
            except NoSuchElementException:
                pass

            tags = []
            count_stale_exception = 0
            while True:
                if count_stale_exception >= 3:
                    without_tag_coins.append(coin)
                else:
                    try:
                        tags = sidebar.find_elements(by=By.XPATH,
                                                     value=".//span[text()='Tags']"
                                                           "//following::div[1]//a")
                        tags = [{'tag': tag.text, 'url': tag.get_attribute('href')} for tag in tags if tags]
                    except NoSuchElementException:
                        pass
                    except StaleElementReferenceException:
                        count_stale_exception += 1
                        print('waiting for StaleElementReferenceException handling...')

                        time.sleep(30)

                        self.driver.get(coin['MainLink'])
                        self.driver.implicitly_wait(5)

                        continue
                break

            coin['tags'] = tags
            coin['github_url'] = github_url

            time.sleep(2)

        return coins, without_tag_coins

    @staticmethod
    def export_to_csv(filename: str, data: list, keys: list):
        with open(filename, 'w', newline='') as file:
            csv_writer = csv.DictWriter(file, fieldnames=keys)
            csv_writer.writeheader()
            csv_writer.writerows(data)

    def get_driver(self):
        return self.driver

    def close(self):
        self.driver.close()
