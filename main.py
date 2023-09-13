import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException, StaleElementReferenceException


class CoinMarketCap(object):
    """
    A class to scrape CoinMarketCap site and extract information about its top
    200 cryptocurrencies on August 28, 2023.
    """

    def __init__(self):
        """Initial the class (opening the Firefox browser)"""
        self.driver = webdriver.Firefox()

    def get_tops(self, url="https://coinmarketcap.com/historical/20230825/"):
        """
        It takes the basic information of the top 200 cryptocurrencies and
        returns it in the form of a list.

        Args:
            url (str, optional): _description_. Defaults to
            "https://coinmarketcap.com/historical/20230825/".

        Returns:
            ``list``:
                A list containing the basic information of each cryptocurrency.
                The basic information of each cryptocurrency is stored as
                a dictionary in this list. This information includes the
                following:
                    - Rank: Cryptocurrency rank.
                    - Name: Cryptocurrency name.
                    - Symbol: Cryptocurrency abbreviation.
                    - MainLink: Link to the special cryptocurrency page on
                        the CoinMarketCap site.
                    - HistoricalLink: Link of the cryptocurrency historical
                        page on the CoinMarketCap site.
        """
        self.driver.get(url)
        self.driver.implicitly_wait(5)
        page_height = self.driver.execute_script("return document.body.scrollHeight")

        for scroll_height in range(0, page_height, 50):
            self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            time.sleep(0.1)

        _coins = self.driver.find_elements(by=By.XPATH, value="//table/tbody/tr")
        coins = []
        for coin in _coins:
            cols = coin.find_elements(by=By.XPATH, value=".//td")
            main_link = (
                cols[1].find_element(by=By.XPATH, value=".//a").get_attribute("href")
            )
            coins.append(
                {
                    "Rank": cols[0].text,
                    "Name": cols[1].text,
                    "Symbol": cols[2].text,
                    "MainLink": main_link,
                    "HistoricalLink": f"{main_link}historical-data/",
                }
            )
        return coins

    def get_history_of_coins(self, coins: list[dict]):
        """
        Download all .csv files containing cryptocurrency information in the last
        365 days (from August 28, 2022 to August 28, 2023).

        Args:
            coins (list[dict]):
                A list containing the basic information of each cryptocurrency
                that we want to download its historical information. If we want
                the historical information of all the top 200 cryptocurrencies,
                we can pass the output of method ``get_tops`` directly to this
                method.
        """
        for coin in coins:
            historical_page_url = coin["HistoricalLink"]
            self.driver.get(historical_page_url)
            self.driver.implicitly_wait(5)
            self.driver.execute_script("window.scrollTo(0, 0);")

            self.driver.find_element(
                by=By.XPATH,
                value="//div[@data-role='btn-content']//*[name()='svg']"
                "/*[name()='use' and @href='#calendar']/parent::*/parent::*",
            ).click()
            self.driver.find_element(
                by=By.XPATH, value="//li[text()='Last 365 days']"
            ).click()
            self.driver.find_element(
                by=By.XPATH, value="//button[text()='Continue']"
            ).click()

            time.sleep(2)

            self.driver.find_element(
                by=By.XPATH, value="//div[contains(text(), 'Download CSV')]"
            ).click()

            time.sleep(2)

    def get_detail_of_coins(self, coins: list[dict]):
        """
        Extracting the link of the Github page and tags related to each
        cryptocurrency, from the special page of that cryptocurrency on the
        site.

        Args:
            coins (list[dict]):
                A list containing the basic information of each cryptocurrency
                that we want to extract the link of the Github page and the tags
                related to it. If we want the link of the Github page and the
                related tags for all top 200 cryptocurrencies, we can pass the
                output of the get_tops method directly to this method.

        Attention:
            Due to the nature of the reviewed site, extracting tags related to
            some cryptocurrencies may encounter errors. In this method, after 3
            attempts to extract the tags, if we fail to extract the tags and
            encounter an error, by handling these errors, we save the
            information of those cryptocurrencies and return them in the output.
            You need to run this method several times (and each time on the
            currencies whose tag extraction failed in the previous step) to
            extract the tags associated with all cryptocurrencies.

        Returns:
            coins (list[dict]):
                A list of basic information about each cryptocurrency, with tags
                and a link to the corresponding Github page.

            without_tag_coins (list[dict]):
                A list of basic information about each cryptocurrency whose tags
                has not been mined.
        """
        without_tag_coins = []
        for coin in coins:
            self.driver.get(coin["MainLink"])
            self.driver.implicitly_wait(5)
            self.driver.execute_script("window.scrollTo(0, 0);")

            sidebar = self.driver.find_element(
                by=By.XPATH, value="//div[contains(@class, 'content_folded')]"
            )

            github_url = None
            try:
                github_url = sidebar.find_element(
                    by=By.XPATH,
                    value=".//span[text()='Official links']"
                    "//following::div[1]"
                    "//a[contains(text(), 'GitHub')]",
                )
                github_url = github_url.get_attribute("href")
            except NoSuchElementException:
                pass

            tags = []
            count_stale_exception = 0
            while True:
                if count_stale_exception >= 3:
                    without_tag_coins.append(coin)
                else:
                    try:
                        tags = sidebar.find_elements(
                            by=By.XPATH,
                            value=".//span[text()='Tags']" "//following::div[1]//a",
                        )
                        tags = [
                            {"tag": tag.text, "url": tag.get_attribute("href")}
                            for tag in tags
                            if tags
                        ]
                    except NoSuchElementException:
                        pass
                    except StaleElementReferenceException:
                        count_stale_exception += 1
                        print("waiting for StaleElementReferenceException handling...")

                        time.sleep(30)

                        self.driver.get(coin["MainLink"])
                        self.driver.implicitly_wait(5)

                        continue
                break

            coin["tags"] = tags
            coin["github_url"] = github_url

            time.sleep(2)

        return coins, without_tag_coins

    @staticmethod
    def export_to_csv(filename: str, data: list, keys: list):
        """
        Creating a .csv file from the scraped data.

        Args:
            filename (str): The name of our .csv file
            data (list): A list of information about each cryptocurrency
            keys (list): The headers of our .csv file
        """
        with open(filename, "w", newline="") as file:
            csv_writer = csv.DictWriter(file, fieldnames=keys)
            csv_writer.writeheader()
            csv_writer.writerows(data)

    def get_driver(self):
        """Get the driver"""
        return self.driver

    def close(self):
        """Close the driver"""
        self.driver.close()
