import re
import time

from bs4 import BeautifulSoup
from sqlalchemy import or_
from sqlalchemy.orm import Query

from app.updaters.base_updater import RowsUpdater
from app.updaters.ikea_parser import get_driver
from app.db import IkeaProduct


class CheckAvailableRowsUpdater(RowsUpdater):
    @staticmethod
    def check_avil(driver, urls):
        driver.delete_all_cookies()
        driver.refresh()

        items = {}

        for url in urls:
            code = re.findall(r"\d+", url)[-1].strip("0")
            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html5lib')
            price = 0
            if soup.find("div", {"data-product-price": True}):
                price = soup.find("div", {"data-product-price": True})["data-product-price"]
            items[code] = {
                "price": price,
                "Личные_заметки": "",
                "avilable": False
            }

            for k in range(4):
                try:
                    driver.find_element_by_class_name("range-revamp-btn--emphasised").click()
                    time.sleep(3)
                    soup = BeautifulSoup(driver.page_source, 'html5lib')
                    if soup.find("div", {"data-product-price": True}):
                        items[code]["price"] = soup.find("div", {"data-product-price": True})["data-product-price"]

                    if soup.find("h3", {"class": "range-revamp-popup__heading"}) and "Ой!" in soup.find("h3", {
                        "class": "range-revamp-popup__heading"}).text:

                        items[code]["avilable"] = False
                        items[code]["Личные_заметки"] = "Ошибка при добавлении в корзину"
                    else:
                        items[code]["avilable"] = True

                    if "30373588" == str(code):
                        driver.save_screenshot(f"30373588.png")

                    break
                except:
                    time.sleep(0.5)
        return items

    model = IkeaProduct
    index_elements = ['url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_query(self):
        return Query(IkeaProduct).filter(
            IkeaProduct.is_failed == False,
            IkeaProduct.ru_data.isnot(None),
            or_(IkeaProduct.pl_data.isnot(None),
                IkeaProduct.ua_data.isnot(None)),
            IkeaProduct.is_available.is_(None))

    def before(self):
        self.driver = get_driver()

    def after(self):
        self.driver.quit()

    def handle_rows(self, rows):
        row_by_code = {
            row.code: row
            for row in rows
        }
        items = self.check_avil(self.driver, [row.url for row in rows])
        for code, item in items.items():
            row = row_by_code[code]
            yield {
                **row.to_dict(),
                'is_available': item.get('avilable', None),
                'data': {**(row.data or {}), 'price': item.get('price')}
            }


if __name__ == '__main__':
    while True:
        CheckAvailableRowsUpdater(limit=5).update()
