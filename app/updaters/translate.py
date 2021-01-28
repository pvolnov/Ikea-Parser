from .base_updater import RowsUpdater
from app.db import IkeaProduct
from app.config import CountryCode


class TranslateProductRowsUpdater(RowsUpdater):

    def before(self):
        pass

    def after(self):
        pass

    def iter_update(self, *args, **kwargs):
        items = self.session.query(IkeaProduct).filter(IkeaProduct.country == CountryCode.PL.value,
                                                  IkeaProduct.is_failed == False,
                                                  IkeaProduct.pl_data.isnot(None),
                                                  IkeaProduct.ru_data.is_(None)).limit(10).all()
        for product in items:
            pl_data = product.pl_data
            to_translate = {
                pl_data['']
            }