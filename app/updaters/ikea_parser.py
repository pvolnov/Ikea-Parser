from contextlib import suppress

from selenium import webdriver
from logdecorator import log_on_error, log_on_end, log_on_start
import logging

from app.logging_config import logger
from app.parser_utils import ParserUtils
from app.db import IkeaProduct, scoped_session, Session, current_session
from app.updaters.base_updater import RowsUpdater
from app.config import PROJECT_DIR, CountryCode
from sqlalchemy.dialects.postgresql import insert


def get_driver():
    return webdriver.Firefox(executable_path=f'{PROJECT_DIR}/data/geckodriver')


class ProductLinksRowsUpdater(RowsUpdater):
    def __init__(self):
        super().__init__()
        self.driver = None

    def before(self):
        self.driver = get_driver()

    def after(self):
        self.driver.quit()

    def add_dicts_props(self, dicts, props):
        return [
            {
                **props,
                **dict_item
            }
            for dict_item in dicts
        ]

    @log_on_start(logging.DEBUG, 'Start saving {country}', logger=logger)
    def insert_cut_products(self, country: CountryCode, items):
        items = self.add_dicts_props(items, {'country': country.value})
        query = insert(IkeaProduct).values(
            items
        ).on_conflict_do_nothing()
        self.session.execute(query)
        self.session.commit()

    def get_product_items(self, categories_url):
        """Each item have format
        {url: <product url>, code: <product code>}
        """
        return ParserUtils.get_items_links(self.driver, categories_url)

    @log_on_start(logging.DEBUG, 'Updating items {country}', logger=logger)
    @log_on_error(logging.DEBUG, 'Error updating items {country}', logger=logger)
    def update_items(self, country: CountryCode):
        category_urls = {
            CountryCode.UA: 'https://www.ikea.com/ua/uk/cat/tovari-products/',
            CountryCode.PL: 'https://www.ikea.com/pl/pl/cat/tovari-products/'
        }

        items = self.get_product_items(category_urls[country])
        logger.info('Found %s products on site', items)
        self.insert_cut_products(country, items)

    def iter_update(self):
        try:
            self.update_items(CountryCode.PL)
        except:
            logger.exception('Fail to update %s links', CountryCode.PL)
        try:
            self.update_items(CountryCode.UA)
        except:
            logger.exception('Fail to update %s links', CountryCode.PL)

    def __del__(self):
        with suppress(Exception):
            self.driver.quet()


if __name__ == '__main__':
    parser = ProductLinksRowsUpdater()
    parser.iter()

