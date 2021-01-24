"""
Класс Переводчика.
Содержит функционал связанный с переводом текстов (пока на русский)
Не должен быть привязан к конкретному парсеру или боту
TODO: Убрать функции относящиеся к парсеру, сделать их чистыми
"""

import re
import time
import requests
from bs4 import BeautifulSoup


class Translator:

    @staticmethod
    def mtranslate(driver, item, tags):
        res = {}
        driver.get(f"https://www.m-translate.ru/translator/text#text=test&direction=pl-ru")
        res["Описание"] = Translator.get_translate_mtranslator(driver, item["Описание"])
        res["Название_позиции"] = Translator.get_translate_mtranslator(driver, item["Название_позиции"])
        tags2 = []
        for t in tags:
            tags2.append(Translator.get_translate_mtranslator(driver, t))
        return res, tags2

    @staticmethod
    def get_translate_mtranslator(driver, text):
        time.sleep(0.2)
        driver.find_element_by_id("text").clear()
        driver.find_element_by_id("text").send_keys(text)
        driver.find_element_by_id("go_btn").click()
        while driver.find_element_by_id("text_out").get_attribute("value") == "":
            time.sleep(0.2)
        return driver.find_element_by_id("text_out").get_attribute("value")

    @staticmethod
    def get_translate(code):
        r = requests.get(f"https://markett.com.ua/site_search?search_term={code}")
        soup = BeautifulSoup(r.text, 'html5lib')
        if not soup.find("li", {"data-product-id": True}):
            return None, None
        itemid = soup.find("li", {"data-product-id": True})["data-product-id"]

        r = requests.get(f"https://markett.com.ua/p{itemid}-ikea-stol-pismennyj.html")
        soup = BeautifulSoup(r.text, 'html5lib')
        data = {}
        data["Название_позиции"] = soup.find("span", {"data-qaid": "product_name"}).text

        discr = ""
        for c in soup.find("div", {"class": "b-user-content"}).children:
            try:
                discr += c.text + "\n"
            except:
                pass
        data["Описание"] = discr

        params = ""
        for tr in soup.tbody.find_all("tr"):
            if len(tr.find_all("td")):
                params += tr.find_all("td")[0].text + ":" + tr.find_all("td")[-1].text + "\n"
        data["Описание"] += "\n" + params

        tags = []
        for li in soup.find_all("li", {"class": "b-path__item"}):
            tags.append(re.sub(r"[\n(\s{2:})(^\s+)]", "", li.text))

        return data, tags[2:-1]
