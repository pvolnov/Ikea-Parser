"""
    Это главный файл. В рабочем режиме, он должен быть всегда запущен
    Если процесса не существует, значит парсер упал. Такого не должно происходить,
    это критический баг.
    Итого чтобы запустить парсер в проде
    python main.py
"""
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from app.logging_config import logger
from app.representers.tgbot import start_pooling
from app.updaters.translate_updater import TranslateUpdater
from app.updaters.check_is_available_updater import CheckAvailableRowsUpdater
import func_timeout
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process


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
            except:
                logger.exception('Task failed %s', func.__name__)

    def start(self):
        with ThreadPoolExecutor() as executor:
            for (func, args, kwargs) in self.tasks:
                executor.submit(self.__infinite_wrapper, func, *args, **kwargs)


if __name__ == '__main__':
    runner = SimpleInfiniteRunner()
    #runner.add(run_updater, TranslateUpdater(limit=10))
    #runner.add(run_updater, CheckAvailableRowsUpdater(limit=10, drivers_count=1))
    runner.add(start_pooling)
    runner.start()
