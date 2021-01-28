from app.db import session_scope
from tqdm import tqdm

from app.logging_config import logger
from scrapy_parser.pipelines import DBUpdaterPipeline


class RowsUpdater:
    proxies = []

    def __init__(self, limit=3):
        self.limit = limit
        self.session = None
        self.rows = []
        self.pipeline = DBUpdaterPipeline(settings={
            'model':  self.model,
            'index_elements': self.index_elements
        })

    def get_query(self):
        raise NotImplementedError

    def make_query(self):
        query = self.get_query()
        if self.limit:
            query = query.limit(self.limit)

        query = query.with_session(self.session)
        # s.execute(rows)
        self.session.expunge_all()
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
