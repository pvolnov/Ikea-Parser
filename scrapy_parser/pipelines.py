# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from colorama import Fore, Style

from app.db import session_scope, IkeaProduct
from app.logging_config import logger
from sqlalchemy.dialects.postgresql import insert


class DBUpdaterPipeline:
    def __init__(self, settings=None):
        self.items = []
        self.settings = settings
        self.model = settings['model']
        self.index_elements = settings.get('index_elements')
        self.bunch_size = 20
        self.index_hashes = set()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings.get('DB_UPDATER_PIPELINE')
        return cls(settings=settings)

    @staticmethod
    def add_dicts_props(dicts, props):
        return [
            {
                **props,
                **dict_item
            }
            for dict_item in dicts
        ]

    @staticmethod
    def get_dicts_keys(dicts):
        return sum([list(d.keys()) for d in dicts], [])

    def upload_items(self):
        if not self.items:
            return
        keys = self.get_dicts_keys(self.items)
        self.items = self.add_dicts_props(self.items, {key: None for key in keys})
        with session_scope() as s:
            insert_query = insert(self.model).values(
                self.items
            )
            set_dict = {
                key: getattr(insert_query.excluded, key)
                for key in keys
            }
            upsert_statement = insert_query.on_conflict_do_update(
                index_elements=self.index_elements,
                set_=set_dict
            )

            s.execute(upsert_statement)
            s.commit()
            self.items = []

    def _get_index_elements_hash(self, item):

        return '.'.join(sorted(str(item.get(name)) for name in self.index_elements))

    def _handle_item(self, item):
        if self._get_index_elements_hash(item) in self.index_hashes:
            logger.info('ПОВТОРЕНИЕ ПО ИНТЕКСУ')
        else:
            self.index_hashes.add(self._get_index_elements_hash(item))
            self.items.append(item)
            if len(self.items) > self.bunch_size:
                self.upload_items()

    def close_spider(self, spider=None):
        self.upload_items()

    def process_item(self, item, spider=None):
        try:
            self._handle_item(item)
        except:
            logger.exception('Wrong item %s', item)


if __name__ == '__main__':
    """Tests completed"""
    pipeline = DBUpdaterPipeline(settings={'model': IkeaProduct, 'index_elements': ['url']})
    pipeline.items = [
        {
            'url': 'www.example.com',
            'code': 'testxxx',
            'country': 'RU',
            'is_new': False
        },
        {
            'url': 'www.example2.ru',
            'code': 'test2',
            'country': 'UA'
        },
        {
            'url': 'www.example3.ru',
            'code': 'sfsdfs',
            'country': 'UA',
            'is_new': True
        }
    ]
    pipeline.upload_items()
    with session_scope() as s:
        rows = s.query(IkeaProduct).filter(IkeaProduct.url.like('%www.example%')).delete(synchronize_session=False)
        print(rows)

if __name__ == '__main__':
    p = DBUpdaterPipeline(settings={'model': IkeaProduct,
                                    'index_elements': ['url']})
    print(p._get_index_elements_hash({'url':123}))
    # p.process_item({'url': 123})
    # p.process_item({'url': 321})