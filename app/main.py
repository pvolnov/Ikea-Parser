"""
    Это главный файл. В рабочем режиме, он должен быть всегда запущен
    Если процесса не существует, значит парсер упал. Такого не должно происходить,
    это критический баг.
    Итого чтобы запустить парсер в проде
    python main.py
"""


def run_parser():
    pass


from app.translator import Translator, Language
from app.ikea_parser.products_parser import ProductsParser
import pyexcel

if __name__ == '__main__':
    lines = [
        {
            'Код товара': 123,
            'Название': 'Подушка'
        },
        {
            'Код товара': 54,
            'Описание': 'Теплая'
        }
    ]
    pyexcel.save_as(records=lines, dest_file_name='../.tmp/file.xlsx')
    # translator = Translator()
    # p_parser = ProductsParser()
    # # p_parser.init_driver()
    # gen = p_parser.translate_pl_generator()
    # res = translator.translate(p_parser.driver, {'name': 'value'}, Language.PL, Language.RU)
    # print(res)
