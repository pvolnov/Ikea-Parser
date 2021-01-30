from sqlalchemy.orm import Query
from termcolor import colored

from app.db import session_scope, IkeaProduct
from tqdm import tqdm

from app.logging_config import logger
from scrapy_parser.pipelines import DBUpdaterPipeline


class RowsUpdater:
    proxies = []

    def __init__(self, *args, limit=3, **kwargs):
        self.limit = limit
        self.session = None
        self.rows = []
        if getattr(self, 'pipeline', None):
            self.pipeline = DBUpdaterPipeline(settings={
                'model':  self.model,
                'index_elements': self.index_elements
            })

    def get_query(self):
        raise NotImplementedError

    def make_query(self):
        query = self.get_query()
        query = query.with_session(self.session)
        # s.execute(rows)
        self.session.expunge_all()
        rows_count = query.count()
        all_rows_count = self.session.query(self.model).count()
        if self.limit:
            query = query.limit(self.limit)
        print(colored(f'Lines left: {rows_count} from {all_rows_count}', 'green'))
        self.rows = query.all()

    def handle_item(self, item):
        logger.debug('Handle item %s', item)
        self.pipeline.process_item(item)

    def update(self):
        with session_scope() as s:
            self.session = s
            if hasattr(self.pipeline, 'open_spider'):
                self.pipeline.open_spider()
            self.before()
            self.make_query()
            print(self.rows)
            if hasattr(self, 'handle_rows'):
                for item in self.handle_rows(self.rows):
                    self.handle_item(item)
            elif hasattr(self, 'handle_row'):
                for row in self.rows:
                    for item in self.handle_row(row):
                        self.handle_item(item)

            self.after()
            if hasattr(self.pipeline, 'close_spider'):
                self.pipeline.close_spider()

    def before(self):
        pass

    def after(self):
        pass

    def __del__(self):
        try:
            self.after()
        except:
            pass


if __name__ == '__main__':
    with session_scope() as s:
        query = Query(IkeaProduct)
        s_query = query.with_session(s)
        print(s_query.count())
        print(s_query.filter(IkeaProduct.country == 'PL').count())
