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

from app.logging_config import logger
from app.representers.tgbot import start_pooling
import func_timeout
from multiprocessing import Process

from scrapy_parser.spiders.productpage import ProductPageSpider


def init_crawler():
    return CrawlerProcess(get_project_settings())


def run_spider(spider):
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


def run_updater(updater, *args, sleep_sec=2, **kwargs):
    while True:
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
                sleep(1)
            except FunctionTimedOut:
                logger.info('FunctionTimedOut %s %s %s', func.__name__, args, kwargs)
            except:
                logger.exception('Task failed %s', func.__name__)

    def start(self):
        with ThreadPoolExecutor() as executor:
            for (func, args, kwargs) in self.tasks:
                executor.submit(self.__infinite_wrapper, func, *args, **kwargs)


if __name__ == '__main__':
    runner = SimpleInfiniteRunner()
    runner.add(run_spider(ProductPageSpider), limit=40)
    runner.start()
