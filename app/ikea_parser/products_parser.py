"""
Это основной цикл обновления товаров с сайта
Интервал 600 секунд между обновлениями
Именно этот файл нужно запускать на сервере (в текущей реализации)
"""

from peewee import EXCLUDED
from tqdm import tqdm
from selenium import webdriver
from enum import Enum
from logdecorator import log_on_error, log_on_end, log_on_start
import logging
from contextlib import suppress

from app.models import UaIkeaItems, PlIkeaItems
from app.logging_config import logger
from app.ikea_parser.parser_utils import ParserUtils
from app.db import IkeaProduct, current_session as s


class CountryCode(Enum):
    UA = 'UA'
    PL = 'PL'


class ProductsParser:
    def __init__(self):
        self.driver = None

    def init_driver(self):
        self.driver = webdriver.Firefox(executable_path='../data/geckodriver')

    def quit_driver(self):
        self.driver.quit()

    @staticmethod
    @log_on_start(logging.DEBUG, 'Start saving {country}', logger=logger)
    def insert_brief_products(country: CountryCode, items):
        ProductsParser.get_model(country).insert_many(items).on_conflict_ignore().execute()

    def get_product_items(self, categories_url):
        """Each item have format
        {url: <product url>, code: <product code>}
        """
        return ParserUtils.get_items_links(self.driver, categories_url)

    @staticmethod
    def parse_product(country: CountryCode, cut_product) -> dict:
        data, tags = ParserUtils.parse_ikea_page(cut_product['url'])
        item = cut_product
        item['data'] = data
        # if country == CountryCode.PL:
        #     item = translate_product(self.driver, item, tags)
        item['tags'] = tags
        return item

    @staticmethod
    def get_model(country: CountryCode):
        return {
            CountryCode.UA: UaIkeaItems,
            CountryCode.PL: PlIkeaItems
        }[country]

    @staticmethod
    def get_items_to_load(country: CountryCode, limit: int = 10):
        model = ProductsParser.get_model(country)
        items = model.select(model.code, model.url).where(model.loaded == False, model.is_failed == False).limit(
            limit).dicts()
        return items

    @staticmethod
    def save_products_batch(country: CountryCode, products: list):
        model = ProductsParser.get_model(country)
        model.insert_many(products).on_conflict(
            conflict_target=[model.code],
            update={
                model.data: EXCLUDED.data,
                model.is_failed: EXCLUDED.is_failed,
                model.loaded: EXCLUDED.loaded,
                model.is_translated: EXCLUDED.is_translated,
            }
        ).execute()

    def fill_products_generator(self, country: CountryCode, batch_size):
        """Get from db not loaded items. Parse pages and fill this lines in db"""
        while True:
            items = list(self.get_items_to_load(country, limit=batch_size))
            products = []
            for item in items:
                product = {
                    **item,
                    'loaded': True,
                    'is_translated': False,
                    'is_failed': False
                }
                try:
                    product.update(self.parse_product(country, item))
                except:
                    product.update({
                        'is_failed': True
                    })

                products.append(product)
            self.save_products_batch(country, products)
            yield len(items)
            if not items:
                return

    @log_on_error(logging.ERROR, 'Error filling products {country}', logger=logger)
    @log_on_end(logging.INFO, 'All products filled {country}', logger=logger)
    def fill_products(self, country: CountryCode):
        model = self.get_model(country)
        cut_products_count = model.select().where(model.loaded == False).count()
        batch_size = 5
        logger.info('items_to_load_count %s', cut_products_count)
        for i in tqdm(self.fill_products_generator(country, batch_size), total=cut_products_count / batch_size):
            pass

    @log_on_start(logging.DEBUG, 'Updating items {country}', logger=logger)
    @log_on_error(logging.DEBUG, 'Error updating items {country}', logger=logger)
    def update_items(self, country: CountryCode):
        category_urls = {
            CountryCode.UA: 'https://www.ikea.com/ua/uk/cat/tovari-products/',
            CountryCode.PL: 'https://www.ikea.com/pl/pl/cat/tovari-products/'
        }

        items = self.get_product_items(category_urls[country])
        logger.info('Found %s products on site', items)
        self.insert_brief_products(country, items)

    def run_update(self):
        self.init_driver()

        for country in CountryCode:
            try:
                self.update_items(country)
            except:
                logger.exception('Fail to update %s products', country)

        self.quit_driver()

    def translate_pl_generator(self, limit=1):
        products = s.query(IkeaProduct).filter(IkeaProduct.country == CountryCode.PL.value,
                                               IkeaProduct.ru_data.is_(None))\
            .limit(limit).count()
        print(products)
        # for product in products:
        #     print(product)
            # data = product.pl_data
            # print(data)

    def __del__(self):
        with suppress(Exception):
            self.quit_driver()


if __name__ == "__main__":
    parser = ProductsParser()
    # parser.init_driver()
    parser.fill_products(CountryCode.PL)
