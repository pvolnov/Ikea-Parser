import re
import time

from bs4 import BeautifulSoup
from sqlalchemy import or_
from sqlalchemy.orm import Query
from tqdm import tqdm

from app.logging_config import logger
from app.modules.selenium import get_driver
from app.updaters.base_updater import RowsUpdater
from app.db import IkeaProduct


class CheckAvailableRowsUpdater(RowsUpdater):
    @staticmethod
    def check_avil(driver, url):
        driver.delete_all_cookies()
        # driver.refresh()
        item = {}
        code = re.findall(r"\d+", url)[-1].strip("0")
        driver.get(url)
        # time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html5lib')
        price = 0
        if soup.find("div", {"data-product-price": True}):
            price = soup.find("div", {"data-product-price": True})["data-product-price"]
        item = {
            "price": price,
            "Личные_заметки": "",
            "avilable": False
        }

        for k in range(4):
            try:
                driver.find_element_by_class_name("range-revamp-btn--emphasised").click()
                time.sleep(2.5)
                soup = BeautifulSoup(driver.page_source, 'html5lib')
                if soup.find("div", {"data-product-price": True}):
                    item["price"] = soup.find("div", {"data-product-price": True})["data-product-price"]

                if soup.find("h3", {"class": "range-revamp-popup__heading"}) and "Ой!" in soup.find("h3", {
                    "class": "range-revamp-popup__heading"}).text:

                    item["avilable"] = False
                    item["Личные_заметки"] = "Ошибка при добавлении в корзину"
                else:
                    item["avilable"] = True

                if "30373588" == str(code):
                    driver.save_screenshot(f"30373588.png")

                break
            except:
                logger.warning('check available wait')
                time.sleep(0.5)
        return item

    model = IkeaProduct
    index_elements = ['url']
    pipeline = True

    def __init__(self, *args, **kwargs):
        self.drivers_count = kwargs.get('drivers_count', 1)
        super().__init__(*args, **kwargs)

    def get_query(self):
        return Query(IkeaProduct).filter(
            IkeaProduct.is_failed == False,
            IkeaProduct.ru_data.isnot(None),
            or_(IkeaProduct.pl_data.isnot(None),
                IkeaProduct.ua_data.isnot(None)),
            IkeaProduct.is_available.is_(None))

    def before(self, *args, **kwargs):
        n_drivers = self.drivers_count
        self.driver = get_driver()
        self.driver.implicitly_wait(1)

        self.drivers = [
            get_driver()
            for i in range(n_drivers)
        ]

    def after(self):
        self.driver.quit()
        # for driver in self.drivers:
        #     driver.quit()

    def handle_row(self, row):
        item = self.check_avil(self.driver, row.url)
        yield {
            **row.to_dict(),
            'is_available': item.get('avilable', None),
            'data': {**(row.data or {}), 'price': item.get('price')}
        }


if __name__ == '__main__':
    for i in tqdm(CheckAvailableRowsUpdater(limit=10)):
        pass
