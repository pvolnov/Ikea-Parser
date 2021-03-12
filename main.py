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
from tqdm import tqdm, trange

from app.logging_config import logger
import func_timeout
from multiprocessing import Process
from scrapy import Spider
from threading import Thread

from app.modules.selenium import Driver
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


def run_updater(updater: RowsUpdater):
    def run(*args, **kwargs):
        for i in trange(updater.limit + 1):
            updater.update(*args, **kwargs)

    return run


class SimpleInfiniteRunner:
    def __init__(self):
        self.tasks = []
        self.threads = []

    def add(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))

    @staticmethod
    def __infinite_wrapper(func, *args, **kwargs):
        while True:
            try:
                func(*args, **kwargs)
            except:
                logger.exception('Task failed %s', func.__name__)

    def start(self):
        threads = []
        with ThreadPoolExecutor() as executor:
            for (func, args, kwargs) in self.tasks:
                threads.append(
                    Thread(target=self.__infinite_wrapper, args=(func, *args), kwargs=kwargs)
                )

    def stop(self):
        for thread in self.threads:
            thread.cancel()

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    limit = 3
    runner = SimpleInfiniteRunner()
    # runner.add(run_spider(LinksSpider), limit=limit, sleep=3600)
    # runner.add(run_spider(ProductPageSpider), sleep=30)
    # runner.add(run_updater(TranslateUpdater(limit=limit)), sleep=20)
    # runner.add(run_updater(CheckAvailableRowsUpdater(limit=limit)), sleep=30)
    # runner.start()
    start_pooling()
