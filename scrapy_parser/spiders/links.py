import scrapy
import re

from scrapy.shell import inspect_response

from app.db import IkeaProduct
from app.logging_config import logger
from scrapy_parser.pipelines import DBUpdaterPipeline
from app.config import CountryCode


class LinksSpider(scrapy.Spider):
    name = 'links'
    allowed_domains = ['www.ikea.com', 'sik.search.blue.cdtapps.com']
    start_urls = []

    custom_settings = {
        'DB_UPDATER_PIPELINE': {
            'model': IkeaProduct,
            'index_elements': ['url']
        },
        'ITEM_PIPELINES': {
            DBUpdaterPipeline: 400
        },
        'HTTPCACHE_ENABLED': False
    }

    def start_requests(self):
        category_urls = {
            CountryCode.UA: 'https://www.ikea.com/ua/uk/cat/tovari-products/',
            CountryCode.PL: 'https://www.ikea.com/pl/pl/cat/tovari-products/'
        }
        for country, url in category_urls.items():
            yield scrapy.Request(url, cb_kwargs={'country': country})

    def parse(self, response, **kwargs):
        # inspect_response(response, spider=self)
        for url in response.css('li a.vn-link.vn-nav__link::attr(href)').getall():
            category_name = url.strip('/').split('/')[-1]
            category_hash = category_name.split('-')[-1]
            page_url = f'{url}?page=20'
            country_stamp = {
                CountryCode.UA: 'ua/uk',
                CountryCode.PL: 'pl/pl'
            }
            category_json_url = 'https://sik.search.blue.cdtapps.com/{}/product-list-page?category={}&size=1000'
            url = category_json_url.format(country_stamp[kwargs.get('country')], category_hash)
            yield scrapy.Request(url, callback=self.parse_category_json, cb_kwargs=kwargs)
            # yield scrapy.Request(page_url, callback=self.parse_products_list, cb_kwargs=kwargs)

    def parse_category_json(self, response, country=None, **kwargs):
        # inspect_response(response, spider=self)
        json = response.json()
        products = json['productListPage']['productWindow']
        category_name = json['productListPage']['category']['name']
        logger.info('Category: %s, find products: %s', category_name, len(products))
        for product in products:
            yield ({
                'url': product['pipUrl'],
                'code': product['id'],
                'country': country.value
            })

    def parse_products_list(self, response, country: CountryCode = None, **kwargs):
        # inspect_response(response, spider=self)
        logger.info('Page category "%s" products: %s',
                    response.css('div.plp-page-title h1.plp-page-title__title::text').get(),
                    len(response.css('div.range-revamp-product-compact__bottom-wrapper a').getall()))
        for url in response.css('div.range-revamp-product-compact__bottom-wrapper a::attr(href)').getall()[:0]:
            yield {
                'url': url,
                'code': re.search(r"\d+", url.split("-")[-1]).group(0).strip("0"),
                'country': country.value
            }
