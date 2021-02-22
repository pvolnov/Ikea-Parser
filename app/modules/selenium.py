from selenium import webdriver

from app.config import PROJECT_DIR, HEROKU
from app.logging_config import logger

__driver = None

# from pyvirtualdisplay import Display
from urllib.parse import urlparse


# display = Display(visible=0, size=(800, 600))
# display.start()


class Driver:
    def __init__(self):
        self.max_tabs_count = 5
        # chrome_options = webdriver.ChromeOptions()
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
        # chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("disable-infobars")
        # chrome_options.add_argument("--disable-extensions")
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option('prefs', prefs)
        # chrome_options.add_argument(f"load-extension={PROJECT_DIR}/data/gighmmpiobklfepjocnamgkkbiglidom.zip")
        # self.driver = webdriver.Chrome(chrome_options=chrome_options,
        #                                executable_path=f'{PROJECT_DIR}/data/chromedriver')
        if HEROKU:
            self.driver = webdriver.PhantomJS()
        else:
            self.driver = webdriver.Firefox(executable_path=f'{PROJECT_DIR}/data/geckodriver')
        self.tabs_dict = {

        }

    def __getattr__(self, item):
        return getattr(self.driver, item)

    def close(self):
        pass
        # display.stop()

    def _new_tab(self):
        if len(self.driver.window_handles) < self.max_tabs_count:
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
