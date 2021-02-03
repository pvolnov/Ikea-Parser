from sqlalchemy.orm import Query

from app.db import session_scope, IkeaProduct, Session

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
        self.__curr_row_index = 0

    def get_query(self):
        raise NotImplementedError

    @property
    def query(self):
        q = self.get_query()
        return q.with_session(self.session)

    def make_query(self):
        q = self.query
        # s.execute(rows)
        self.session.expunge_all()
        # rows_count = query.count()
        # all_rows_count = self.session.query(self.model).count()
        if self.limit:
            q = q.limit(self.limit)
        # print(colored(f'Lines left: {rows_count} from {all_rows_count}', 'green'))
        self.rows = q.all()

    def all_count(self, session):
        return session.query(self.model).count()

    def remaining_count(self):
        self._update_session()
        return self.query.count()

    def handle_item(self, item):
        logger.debug('Handle item %s', item)
        self.pipeline.process_item(item)

    def __len__(self):
        return self.remaining_count()

    def __next__(self):
        for item in self.handle_row(self._get_row()):
            self.handle_item(item)

    def _update_session(self):
        if self.session:
            try:
                self.session.commit()
            except:
                self.session.rollback()
        self.session = Session()

    def _begin_bunch(self):
        self._update_session()
        self.before()
        if hasattr(self.pipeline, 'open_spider'):
            self.pipeline.open_spider()
        self.before()
        self.make_query()
        self.__curr_row_index = 0

    def _get_row(self):
        self.__curr_row_index += 1
        if self.__curr_row_index > self.limit:
            self._end_bunch()
            self._begin_bunch()
        return self.rows[self.__curr_row_index - 1]

    def _end_bunch(self):
        self.after()
        if hasattr(self.pipeline, 'close_spider'):
            self.pipeline.close_spider()

    def __iter__(self):
        self._begin_bunch()
        return self

    def update(self):
        self._begin_bunch()
        if hasattr(self, 'handle_rows'):
            for item in self.handle_rows(self.rows):
                self.handle_item(item)

        elif hasattr(self, 'handle_row'):
            for row in self.rows:
                for item in self.handle_row(row):
                    self.handle_item(item)

        self._end_bunch()

    def before(self):
        pass

    def after(self):
        pass

    def __del__(self):
        try:
            self._end_bunch()
        except:
            pass


if __name__ == '__main__':
    with session_scope() as s:
        query = Query(IkeaProduct)
        s_query = query.with_session(s)
        print(s_query.count())
        print(s_query.filter(IkeaProduct.country == 'PL').count())
