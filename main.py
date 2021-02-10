"""
    Это главный файл. В рабочем режиме, он должен быть всегда запущен
    Если процесса не существует, значит парсер упал. Такого не должно происходить,
    это критический баг.
    Итого чтобы запустить парсер в проде
    python main.py
"""

from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

from func_timeout import FunctionTimedOut
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tqdm import tqdm

from app.logging_config import logger
import func_timeout
from multiprocessing import Process
from scrapy import Spider

from app.representers.tgbot import start_pooling
from app.updaters.base_updater import RowsUpdater
from app.updaters.translate_updater import TranslateUpdater
from app.updaters.check_is_available_updater import CheckAvailableRowsUpdater

from scrapy_parser.spiders.productpage import ProductPageSpider
from scrapy_parser.spiders.links import LinksSpider


def init_crawler():
    return CrawlerProcess(get_project_settings())


def run_spider(spider: type(Spider)):
    def create_spider_process(*args, **kwargs):
        crawler = init_crawler()
        crawler.crawl(spider, *args, **kwargs)
        crawler.start()
        crawler.stop()

    def run(*args, **kwargs):
        p = Process(target=create_spider_process, kwargs=kwargs, args=args)
        p.start()
        p.join()

    return run


def run_updater(updater: RowsUpdater, *args, sleep_sec=2, **kwargs):
    for i in tqdm(updater):
        updater.update(*args, **kwargs)
        sleep(sleep_sec)


class SimpleInfiniteRunner:
    def __init__(self):
        self.tasks = []

    def add(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))

    @staticmethod
    def __infinite_wrapper(func, *args, **kwargs):
        timeout = 60 * 30  # 30 минут
        while True:
            try:
                func_timeout.func_timeout(timeout, func, args=args, kwargs=kwargs)
                sleep(kwargs.get('sleep', 1))
            except FunctionTimedOut:
                logger.info('FunctionTimedOut %s %s %s', func.__name__, args, kwargs)
            except:
                logger.exception('Task failed %s', func.__name__)

    def start(self):
        with ThreadPoolExecutor() as executor:
            for (func, args, kwargs) in self.tasks:
                executor.submit(self.__infinite_wrapper, func, *args, **kwargs)


if __name__ == '__main__':
    limit = 10
    runner = SimpleInfiniteRunner()
    runner.add(start_pooling)
    # runner.add(run_spider(LinksSpider), limit=limit, sleep=3600)
    # runner.add(run_spider(ProductPageSpider), sleep=30)
    # runner.add(run_updater(TranslateUpdater(limit=limit)), sleep=10)
    # runner.add(run_updater(CheckAvailableRowsUpdater(limit=limit)), sleep=30)
    runner.start()
