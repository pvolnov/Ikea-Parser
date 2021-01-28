import scrapy
import re
from scrapy_parser.pipelines import DBUpdaterPipeline
from app.config import CountryCode


class LinksSpider(scrapy.Spider):
    name = 'links'
    allowed_domains = ['www.ikea.com']
    start_urls = []

    custom_settings = {
        'ITEM_PIPELINES': {
            DBUpdaterPipeline: 400
        }
    }

    def start_requests(self):
        category_urls = {
            CountryCode.UA: 'https://www.ikea.com/ua/uk/cat/tovari-products/',
            CountryCode.PL: 'https://www.ikea.com/pl/pl/cat/tovari-products/'
        }
        for country, url in category_urls.items():
            yield scrapy.Request(url, cb_kwargs={'country': country})

    def parse(self, response, **kwargs):
        for url in response.css('li a.vn-link.vn-nav__link::attr(href)').getall():
            page_url = f'{url}?page=20'
            yield scrapy.Request(page_url, callback=self.parse_products_list, cb_kwargs=kwargs)

    def parse_products_list(self, response, country: CountryCode = None, **kwargs):
        for url in response.css('div.range-revamp-product-compact__bottom-wrapper a::attr(href)').getall()[:0]:
            yield {
                'url': url,
                'code': re.search(r"\d+", url.split("-")[-1]).group(0).strip("0"),
                'country': country.value
            }
