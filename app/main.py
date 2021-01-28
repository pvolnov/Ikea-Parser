"""
    Это главный файл. В рабочем режиме, он должен быть всегда запущен
    Если процесса не существует, значит парсер упал. Такого не должно происходить,
    это критический баг.
    Итого чтобы запустить парсер в проде
    python main.py
"""
from scrapy.crawler import CrawlerRunner, CrawlerProcess
from twisted.internet import reactor, defer
from scrapy.utils.project import get_project_settings

from app.translator import Translator, Language
from scrapy_parser.spiders.productpage import ProductPageSpider
from scrapy_parser.spiders.translate import TranslateSpider
from app.task_manager import Task, TaskManager
from datetime import timedelta
from scrapy import Spider
import scrapy
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


if __name__ == '__main__':
    manager = TaskManager(update_interval=0.1)
    # manager.add_task(
    #     Task('Load ikea product page', run_spider(ProductPageSpider), kwargs={'limit': 100},
    #          interval=timedelta(seconds=10)))
    # manager.add_task(
    #     Task('Load ikea product page', run_spider(TranslateSpider), kwargs={'limit': 1},
    #          interval=timedelta(seconds=60)))
    # manager.start()
