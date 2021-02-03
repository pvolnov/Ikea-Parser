import time
from enum import Enum
from random import randint

import requests
from func_timeout import FunctionTimedOut
from sqlalchemy import or_
from sqlalchemy.orm import Query
from tqdm import tqdm

from app.logging_config import logger
from app.updaters.base_updater import RowsUpdater
from app.updaters.ikea_parser import get_driver
from app.db import IkeaProduct
from app.utils import get_dict, stringify
import func_timeout


class Language(Enum):
    RU = 'ru'
    UA = 'uk'
    PL = 'pl'
    EN = 'en'


class BaseTranslator:
    def translate_to(self, texts, target_lang: Language = None, source_lang: Language = None):
        raise NotImplementedError

    @staticmethod
    def does_support_lang(target_lang: Language, source_lang: Language):
        return True


class SeleniumMTranslateTranslator(BaseTranslator):
    def __init__(self, driver=None):
        self.driver = driver or get_driver()

    @staticmethod
    def does_support_lang(target_lang: Language, source_lang: Language):
        return target_lang == Language.RU and source_lang == Language.PL

    def translate_to(self, texts, target_lang=Language.RU, source_lang=None):
        if target_lang != Language.RU:
            raise NotImplementedError
        items = {
            self.translate_pl_ru(text)
            for text in texts
        }
        return [item.strip() for item in items]

    def translate_pl_ru(self, text, retries_count=0):
        self.driver.get(f"https://www.m-translate.ru/translator/text#text={text}&direction=pl-ru")
        time.sleep(0.2)
        self.driver.find_element_by_id("text").clear()
        self.driver.find_element_by_id("text").send_keys(text)
        self.driver.find_element_by_id("go_btn").click()
        while self.driver.find_element_by_id("text_out").get_attribute("value") == "":
            time.sleep(0.2)
        return self.driver.find_element_by_id("text_out").get_attribute("value")

    def __del__(self):
        self.driver.close()


class SeleniumPerevodTranslator(BaseTranslator):
    lang_pairs = {
        (Language.PL, Language.UA): 'https://perevod.i.ua/polsko-ukrainskiy/',
        (Language.PL, Language.RU): 'https://perevod.i.ua/polsko-russkiy/',
        (Language.UA, Language.RU): 'https://perevod.i.ua/ukrainsko-russkiy/',
        (Language.RU, Language.EN): 'https://perevod.i.ua/russko-angliyskiy/',
    }

    def __init__(self, driver=None):
        self.driver = driver or get_driver()
        self.driver.implicitly_wait(1)

        self.url = ''

    @classmethod
    def does_support_lang(cls, target_lang: Language, source_lang: Language):
        return (source_lang, target_lang) in cls.lang_pairs

    def translate_to(self, texts, target_lang=None, source_lang=None):
        lang_pair = (source_lang, target_lang)
        url = self.lang_pairs[lang_pair]
        return [
            self.translate(url, text)
            for text in texts
        ]

    def translate(self, url, text):
        self.driver.get(url, )
        time.sleep(0.2)
        self.driver.find_element_by_id("first_textarea").clear()
        self.driver.find_element_by_id("first_textarea").send_keys(text)
        self.driver.find_element_by_name("commit").click()
        while self.driver.find_element_by_id("second_textarea").get_attribute("value") == "":
            time.sleep(0.2)
        return self.driver.find_element_by_id("second_textarea").get_attribute("value")

    def __del__(self):
        self.driver.quit()


class YandexApiTranslator(BaseTranslator):
    def __init__(self):
        self.URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        self.API_KEY = 'AQVNz7AiSpbBHL8ZbmsJhwMsSFpOxVMZzWr6aWzc'

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.API_KEY}"
        }

    def translate_to(self, texts: list, target_lang: Language = None, source_lang: Language = None):
        if not texts:
            return texts

        body = {
            "folder_id": 'b1gpf6j6ejlihe9f4j2m',
            "texts": texts,
            "targetLanguageCode": target_lang.value
        }
        response = requests.post(self.URL, json=body, headers=self.headers)
        try:
            translations = response.json()['translations']
        except:
            logger.exception('Fail to translate with yandex. response: %s', response.json())
            raise
        return [tr['text'] for tr in translations]


class TranslatorsLibTranslator(BaseTranslator):
    def translate_to(self, texts, target_lang: Language = None, source_lang: Language = None):
        return [
            self.translate_text(text, target_lang=target_lang, source_lang=source_lang)
            for text in texts
        ]

    @staticmethod
    def translate_text(text, target_lang: Language):
        import translators as ts
        translators = [
            ts.google,
            ts.alibaba,
            ts.bing,
        ]
        for i in range(3):
            for translator_func in translators:
                try:
                    return func_timeout.func_timeout(
                        15, translator_func, args=(text,),
                        kwargs={
                            'if_use_cn_host': True,
                            'to_language': target_lang.value
                        }
                    )
                except FunctionTimedOut:
                    pass
                except:
                    pass
            time.sleep((i + 1) * randint(20, 30))
        raise Exception('Translation failed')


class TranslatorAdapter:
    """This class is highly api to translate any texts"""

    translators = {
        'translators': TranslatorsLibTranslator,
        'mtranslate': SeleniumMTranslateTranslator,
        'perevol': SeleniumPerevodTranslator,
        'yandex': YandexApiTranslator,
    }
    translators_order = [
        'perevol',
        'mtranslate',
        'translators'
    ]

    def __init__(self):
        pass

    def _translate_list_to(self, texts, *args, **kwargs):
        if not texts:
            return []

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_num = {executor.submit(self._translate_list_to, [text], *args, **kwargs): i
                          for i, text in enumerate(texts)}
            translated_dicts = [None] * len(texts)
            for future in as_completed(future_num):
                translated_dicts[future_num[future]] = future.result()
            assert all([item is not None for item in translated_dicts])

            return translated_dicts

    def translate_list_to(self, texts: list, target_lang: Language = None, source_lang: Language = None):
        assert isinstance(texts, list)
        assert len(texts) > 0
        assert isinstance(texts[0], str)
        translated_texts = []
        for tr_name in self.translators_order:
            Translator = self.translators[tr_name]
            if not Translator.does_support_lang(target_lang=target_lang, source_lang=source_lang):
                continue
            try:
                translated_texts = Translator().translate_to(texts, target_lang=target_lang, source_lang=source_lang)
                logger.debug(f'used translator - %s', tr_name)
                break
            except:
                pass
        try:
            assert len(translated_texts) == len(texts), f'result: {translated_texts}, source: {texts}'
        except:
            logger.exception('Translate texts size not equal. target_lang %s, source_lang %s', target_lang, source_lang)
            raise
        if not translated_texts:
            raise Exception('Every translator failed')
        return translated_texts

    def translate_dict_to(self, dict_texts: dict, target_lang: Language = None, source_lang: Language = None):
        items = list(dict_texts.items())
        texts = [item[1] for item in items]
        if not dict_texts:
            return {}

        translated_texts = self.translate_list_to(texts, target_lang=target_lang, source_lang=source_lang)

        return {
            item[0]: translation
            for item, translation in zip(items, translated_texts)
        }

    def translate(self, text, target_lang: Language, source_lang: Language = None):
        return self.translate_list_to([text], target_lang=target_lang, source_lang=source_lang)[0]

    def translate_dicts(self, dicts: list, *args, **kwargs):
        big_dict = {}
        for i, dict_item in enumerate(dicts):
            big_dict.update(
                {
                    (i, key): value
                    for key, value in dict_item.items()
                }
            )
        translated_dict = self.translate_dict_to(big_dict, *args, **kwargs)
        resolved_dicts = [{} for d in dicts]
        for (i, key), value in translated_dict.items():
            resolved_dicts[i][key] = value

        return resolved_dicts


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

