import time
from contextlib import suppress

from selenium import webdriver
from logdecorator import log_on_error, log_on_end, log_on_start
import logging

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from app.logging_config import logger
from app.parser_utils import ParserUtils
from app.db import IkeaProduct, scoped_session, Session
from app.updaters.base_updater import RowsUpdater
from app.config import PROJECT_DIR, CountryCode
from sqlalchemy.dialects.postgresql import insert

__driver = None

from pyvirtualdisplay import Display

display = Display(visible=0, size=(800, 600))
display.start()

class Driver:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2, 'javascript': 2,
                                                            'plugins': 2, 'popups': 2, 'geolocation': 2,
                                                            'css': 2,
                                                            'notifications': 2, 'auto_select_certificate': 2,
                                                            # 'fullscreen': 3,
                                                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2,
                                                            'media_stream_mic': 2, 'media_stream_camera': 2,
                                                            'protocol_handlers': 2,
                                                            'ppapi_broker': 2, 'automatic_downloads': 2,
                                                            'midi_sysex': 2,
                                                            'push_messaging': 2, 'ssl_cert_decisions': 2,
                                                            'metro_switch_to_desktop': 2,
                                                            'protected_media_identifier': 2, 'app_banner': 2,
                                                            'site_engagement': 2,
                                                            'durable_storage': 2}}
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("headless")
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_argument(f"load-extension={PROJECT_DIR}/data/gighmmpiobklfepjocnamgkkbiglidom.zip")
        self.driver = webdriver.Chrome(chrome_options=chrome_options,
                                       executable_path=f'{PROJECT_DIR}/data/chromedriver')
        # self.driver = webdriver.Firefox(executable_path=f'{PROJECT_DIR}/data/geckodriver')
        self.tabs_dict = {

        }

    def __getattr__(self, item):
        return getattr(self.driver, item)

    def close(self):
        display.stop()

    def _new_tab(self):
        self.driver.execute_script("window.open('');")

    def _get_tab(self, url):
        if url not in self.tabs_dict:
            self._new_tab()
            self.tabs_dict[url] = self.driver.window_handles[-1]
        return self.tabs_dict.get(url)

    def _is_equal_urls(self, u1, u2):
        def normalize(u):
            return u.strip('/').replace('//wwww.', '//')

        return normalize(u1) == normalize(u2)

    def get(self, url):
        self.driver.switch_to.window(self._get_tab(url))
        if not self._is_equal_urls(self.driver.current_url, url):
            logger.debug('load %s, curr %s', url, self.driver.current_url)
            self.driver.get(url)

    def quit(self):
        pass

    def __del__(self):
        self.driver.close()


def get_driver():
    global __driver
    if not __driver:
        __driver = Driver()
    return __driver


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
