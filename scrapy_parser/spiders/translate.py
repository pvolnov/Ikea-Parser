import scrapy

from app.db import IkeaProduct, session_scope
from sqlalchemy import or_
from scrapy_parser.pipelines import DBUpdaterPipeline
import json


class TranslateSpider(scrapy.Spider):
    name = 'translate'
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

    def get_urls(self, limit=2):
        with session_scope() as s:
            urls = s.query(IkeaProduct).filter(IkeaProduct.ru_data.is_(None),
                                               IkeaProduct.is_failed == False,
                                               or_(
                                                   IkeaProduct.pl_data.isnot(None),
                                                   IkeaProduct.ua_data.isnot(None)
                                               ))
            if limit:
                urls = urls.limit(limit)
            items = urls.all()
            s.expunge_all()
            return items

    def start_requests(self):
        for row in self.get_urls(getattr(self, 'limit', 2)):
            request = self.yield_translation(row)
            if request:
                yield request

    def parse_translation(self, response, row: IkeaProduct = None, items=None):
        result_json = response.json()
        translations = result_json['translations']
        translated_dict = {
            items[i][0]: translations[i]['text']
            for i in range(len(items))
        }

        yield {
            **row.to_dict(),
            'ru_data': translated_dict
        }

    def get_translate_request(self, texts_dict: dict, row=None, **kwargs):
        items = list(texts_dict.items())
        texts = [item[1] for item in items]

        url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        api_key = 'AQVNz7AiSpbBHL8ZbmsJhwMsSFpOxVMZzWr6aWzc'

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {api_key}"
        }

        body = {
            "folder_id": 'b1gpf6j6ejlihe9f4j2m',
            "texts": texts,
            "targetLanguageCode": "ru"
        }
        return scrapy.Request(url, body=json.dumps(body), method='POST', headers=headers,
                              callback=self.parse_translation, cb_kwargs={
                'row': row,
                'items': items
            })

    def yield_translation(self, row: IkeaProduct = None, **kwargs):
        data = row.pl_data or {}
        data.update(row.ua_data or {})
        translate_fields = ['Описание', 'Название_позиции']
        ru_data = row.ru_data or {}
        fields_to_translate = [
            field for field in translate_fields
            if field not in ru_data and field in data
        ]
        if not fields_to_translate:
            return None
        translate_dict = {
            field: data[field]
            for field in fields_to_translate
        }

        return self.get_translate_request(translate_dict, row=row)
