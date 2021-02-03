import re

import scrapy
from bs4 import BeautifulSoup
from app.db import session_scope, IkeaProduct
from scrapy_parser.pipelines import DBUpdaterPipeline


class ProductPageSpider(scrapy.Spider):
    name = 'productpage'
    allowed_domains = ['www.ikea.com']

    custom_settings = {
        'DB_UPDATER_PIPELINE': {
            'model': IkeaProduct,
            'index_elements': ['url']
        },
        'ITEM_PIPELINES': {
            DBUpdaterPipeline: 400
        }
    }

    def get_urls(self, limit=10):
        with session_scope() as s:
            urls = s.query(IkeaProduct).filter(IkeaProduct.data.is_(None),
                                               IkeaProduct.pl_data.is_(None),
                                               IkeaProduct.is_failed == False,
                                               IkeaProduct.ru_data.is_(None))
            if limit:
                urls = urls.limit(limit)
            items = urls.all()
            s.expunge_all()
            return items

    def __init__(self, *args, limit=10, **kwargs):
        self.limit = limit
        super().__init__(*args, **kwargs)

    def start_requests(self):
        print('LIMIT', getattr(self, 'limit', 10))
        for row in self.get_urls(getattr(self, 'limit', 10)):
            yield scrapy.Request(row.url, cb_kwargs={'row': row})

    def parse(self, response, row: IkeaProduct = None):
        try:
            data = {
                "Тип_товара": "r",
                "Валюта": "UAH",
                "Примечание": "UAH",
                "Единица_измерения": "шт"
            }

            page = response.text
            soup = BeautifulSoup(page, 'html5lib')

            data["Код_товара"] = re.search(r"\d+", row.url.split("-")[-1]).group(0)

            data["Описание"] = soup.find("meta", {"name": "description"})["content"]
            data["Название_позиции"] = data["Описание"].split(".")[0]
            data["Поисковые_запросы"] = soup.find("meta", {"name": "keywords"})["content"]
            data["Цена"] = soup.find("div", {"data-product-price": True})["data-product-price"]
            images = [i['src'] for i in soup.find_all("img", {"class": "range-revamp-aspect-ratio-image__image"})]
            data["Ссылка_изображения"] = ", ".join(images[:9])

            details = ""

            if soup.dl:
                for p in soup.find("dl").find_all("div"):
                    details += p.dt.text.replace("\xa0", "") + " " + p.dd.text + "\n"
            else:
                for p in soup.find_all("span", {"class": "range-revamp-product-details__label"}):
                    details += p.text.replace("\n", "").replace("  ", "") + "\n"

            data["Описание"] += "\n" + details
            if soup.find("div", {"id": "SEC_product-details-material-and-care"}):
                data["Описание"] += "\n" + "\n".join(
                    [d.text for d in soup.find("div", {"id": "SEC_product-details-material-and-care"}).find_all("div")])

            tags = [l.span.text for l in soup.find_all("li", {"class": "bc-breadcrumb__list-item"})]
            data['tags'] = tags

            data_key = {
                'PL': 'pl_data',
                'UA': 'ua_data'
            }[row.country]
            yield {
                **row.to_dict(),
                data_key: data,
            }
        except:
            yield {
                **row.to_dict(),
                'is_failed': True
            }
