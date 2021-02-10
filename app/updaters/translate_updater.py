"""
Класс Переводчика.
Содержит функционал связанный с переводом текстов
Не должен быть привязан к конкретному парсеру или боту
TODO: Убрать функции относящиеся к парсеру, сделать их чистыми
"""

from sqlalchemy import or_
from sqlalchemy.orm import Query
from tqdm import tqdm

from app.updaters.base_updater import RowsUpdater
from app.db import IkeaProduct
from app.modules.translate import TranslatorAdapter, Language
from app.utils import get_dict, stringify


class TranslateUpdater(RowsUpdater):
    model = IkeaProduct
    index_elements = ['url']
    pipeline = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = TranslatorAdapter()

    def get_query(self):
        return Query(IkeaProduct).filter(
            IkeaProduct.is_failed == False,
            or_(
                IkeaProduct.pl_data.isnot(None),
                IkeaProduct.ua_data.isnot(None),
            ),
            or_(

                IkeaProduct.ua_data.is_(None),
                IkeaProduct.ru_data.is_(None),
            )
        )

    def translate_row(self, data: dict):
        fields = ['Название_позиции', 'Описание', 'Поисковые_запросы']

        dict_to_translate = {
            field: stringify(data[field])
            for field in fields
            if field in data and data[field]
        }
        return dict_to_translate

    def handle_row(self, row: IkeaProduct):
        source = {}
        source_lang = Language.RU
        if row.pl_data:
            source = row.pl_data
            source_lang = Language.PL
        elif row.ua_data:
            source = row.ua_data
            source_lang = Language.UA

        ru_data = {}
        ua_data = {}

        data = self.translate_row(source)
        if not row.ru_data:
            ru_data = self.translator.translate_dict_to(data, source_lang=source_lang,
                                                        target_lang=Language.RU)
        if not row.ua_data:
            ua_data = self.translator.translate_dict_to(data, source_lang=source_lang,
                                                        target_lang=Language.UA)
        assert isinstance(ua_data, dict)
        assert isinstance(ru_data, dict)

        yield {
            **row.to_dict(),
            'ru_data': {**get_dict(row.ru_data), **ru_data},
            'ua_data': {**get_dict(row.ua_data), **ua_data},
        }


if __name__ == '__main__':
    for i in tqdm(TranslateUpdater(limit=10)):
        pass

