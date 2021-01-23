import configparser
import re
import time
from contextlib import suppress

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playhouse.shortcuts import model_to_dict
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.select import Select

from bot.models import IkeaItems, Tasks

config = configparser.RawConfigParser()
config.read('config.conf')
course = float(config.get("SETTING", "course"))

bad_cats = [
    "Еда и напитки",
    "Комнатные растения и суккуленты",
]


class Parser:
    modal_accept = 0

    def __init__(self, driver=None, server_url='http://185.69.152.163:4444/wd/hub'):
        self.driver = driver
        self.server_url = server_url
        self.groups_lists = []

    def update_items_tasks(self):
        items_urls = []
        self.driver.get("https://www.ikea.com/pl/pl/")
        page = self.driver.page_source
        soup = BeautifulSoup(page, 'html5lib')
        subparts = []
        parts = []

        for a in soup.find_all("a", {"href": lambda x: x and "cat" in x}):
            parts.append(a["href"])
        parts = list(set(parts))

        for part_url in parts:
            self.driver.get(part_url)
            page = self.driver.page_source
            soup = BeautifulSoup(page, 'html5lib')
            for a in soup.find_all("a", {"class": "range-catalog-list__link"}):
                subparts.append(a["href"])

        parts = subparts.copy()
        subparts = []

        for part_url in parts:
            self.driver.get(part_url)
            page = self.driver.page_source
            soup = BeautifulSoup(page, 'html5lib')
            for a in soup.find_all("a", {"class": "range-catalog-list__link"}):
                subparts.append(a["href"])

        print("subparts:", len(subparts))

        for url in subparts:
            try:
                sub = self.get_items_list(url)
                items_urls += sub
                sub = [{"url": s["url"]} for s in sub]
                Tasks.insert_many(sub).on_conflict_ignore().execute()
                print(f"Find {len(sub)} items")
            except WebDriverException as e:
                self.driver = webdriver.Remote(
                    command_executor=self.server_url,
                    desired_capabilities=DesiredCapabilities.FIREFOX)
                print("Error getting items", e)

        IkeaItems.update({IkeaItems.correct: False}).where(IkeaItems.url.not_in(items_urls)).execute()

        return items_urls

    def update_available(self, url):
        try:
            self.driver.get(url)
            time.sleep(1)
            with suppress(Exception):
                self.driver.execute_script('window.scroll(0,1600)')
                time.sleep(1)
            with suppress(Exception):
                self.driver.execute_script('document.getElementById("find-product").click()')
                time.sleep(1)

            if self.modal_accept < 1000:
                time.sleep(1)
                nn = 1000
                while nn < 3000:
                    try:
                        s = Select(self.driver.find_element_by_id("new-stockcheck-dropdown"))
                        s.select_by_value("311")
                        self.modal_accept += 1
                        time.sleep(1)
                        break
                    except Exception as e:
                        with suppress(Exception):
                            self.driver.find_element_by_id("ikeaTermsConsentModalAccept").click()
                            time.sleep(1)
                        nn += 150
                        self.driver.execute_script(f'window.scroll(0,{nn})')
                        time.sleep(2)
                        print(e)

            page = self.driver.page_source
            soup = BeautifulSoup(page, 'html5lib')

            if soup.find("span", {"class": "range-stock-info__text--bold"}):
                return soup.find("span", {"class": "range-stock-info__text--bold"}).text
            else:
                if "http-status-message__heading h3" in page:
                    IkeaItems.delete().where(IkeaItems.url == url).execute()
                    Tasks.delete().where(Tasks.url == url).execute()
                    print("page not found:", url)
                elif "range-svg-icon range-svg-icon--150 range-stock-icon__stock-out range-icon-section__icon" in page:
                    return "0"
                else:
                    print("page updating available error")
                    self.modal_accept = 0
                    return "e"

        except WebDriverException as e:
            time.sleep(2)
            self.driver = webdriver.Remote(
                command_executor=self.server_url,
                desired_capabilities=DesiredCapabilities.FIREFOX)
            print("Error getting items", e)
            return self.update_available(url)

    def parse_ucr_item_price(self, code):
        r = requests.get("https://sik.search.blue.cdtapps.com/ua/uk/search-box", params={
            "q": code}).json()
        if len(r['searchBox']['products']):
            page = requests.get(r['searchBox']['products'][0]['pipUrl']).text
            soup = BeautifulSoup(page, 'html5lib')
            return soup.find("span", {"class": "range-revamp-price__integer"}).text.replace(" ", "")
        else:
            return "0"

    def parse_item(self, url):
        data = {}
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html5lib')

        try:
            data["name"] = soup.h1.find_all("span")[0].text
            data["surname"] = soup.h1.find_all("span")[1].text
            price = soup.find("span", {"class": "range-revamp-price__integer"})
            data["price"] = price.text if price else "0"

            data["discr"] = soup.find("meta", {"name": "description"})["content"]

            details = soup.find("div", {"id": "range-revamp-product-details__paragraph"})
            data["details"] = details.text if details else ""

            data["rules"] = soup.find("a", {"class": "range-expandable__paragraf"})["href"] if soup.find("a", {
                "class": "range-expandable__paragraf"}) else ""

            imgs = soup.find_all("img", {"class": "carousel-bullets__bullet__image"})
            imgs = [img["src"].replace("f=s", "f=l") for img in imgs]
            data["url"] = url

            for d in data:
                try:
                    data[d] = str(re.sub(r"[\s:]\n", " ", data[d])).replace("  ", "").replace("\xa0", " ")
                except:
                    print(d)

            if soup.find("ol", {"class": "range-breadcrumb__list"}):
                tags = []
                for a in soup.find("ol", {"class": "range-breadcrumb__list"}).find_all("a"):
                    tags.append(a.span.text)
                data["tags"] = tags

            if len(imgs) == 0:
                imgs = [soup.find("div", {"class": "range-carousel__image"}).img["src"]]
            data["imgs"] = imgs

            return data
        except Exception as e:
            print("Error:", url, e)
            print(data)
            return None

    def get_items_list(self, url):
        url += "?page=180"
        self.driver.get(url)
        page = self.driver.page_source

        soup = BeautifulSoup(page, 'html5lib')
        items = []
        divs = soup.find_all("div", {"class": "product-compact"})
        for div in divs:
            items.append({
                "url": div.a["href"],
                "id": div["data-ref-id"],
                #             "position":div["data-list-position"],
                "price": div["data-price"]
            })
        return items

    def to_shop_format(self, item):
        assert len(self.groups_lists), "groups_lists is empty"
        item["price"] = item["price"].replace(" ", "")

        item["price"] = re.search(r"\d+.?\d*", item["price"]).group(0)
        cost = float(item["price"].replace(",", "."))
        ukr_price = float(item["ukr_price"].replace(",", "."))

        for o in config.options("MARGIN"):
            if cost < float(o):
                cost *= float(config.get("MARGIN", o))
                break
        item["price"] = str(int(cost))

        data = {}
        data["Код_товара"] = item["code"]
        data["Название_позиции"] = item["name"]
        data["Поисковые_запросы"] = item["search"]
        data["Описание"] = item["discr"]
        data["Тип_товара"] = "r"
        data["Цена"] = item["price"]
        data["Валюта"] = "UAH"
        data["Единица_измерения"] = "шт"

        if cost * 6.6 * 1.1 >= ukr_price > 0:
            data["Тип_товара"] = "w"
        else:
            data["Тип_товара"] = "r"

        if item["avilable"] == "e" or item["avilable"] == "":
            data["Количество"] = 0
        else:
            data["Количество"] = int(item["avilable"])
        if item["new"]:
            data["Наличие"] = "&"
        else:
            data["Наличие"] = "+" if data["Количество"] > 0 else "-"

        data["Ссылка_изображения"] = item["image"]
        data["Идентификатор_товара"] = item["code"]
        if len(item["tags"]) > 1:
            data["Идентификатор_группы"] = int(self.groups_lists.index(item["tags"][-2]))
        return data

    def save_to_db(self, item):
        data = {}
        item["avilable"] = "0"
        data["code"] = item["id"]
        data["tags"] = item["tags"]
        data["url"] = item["url"]
        data["name"] = item["name"] + item["surname"]
        if len(item["tags"]) > 2:
            data["search"] = item["tags"][-2]
        else:
            print(item["tags"])
        data["discr"] = item["discr"] + "\n" + item["dimensions"] + "\n" + item["material"]
        data["price"] = item["price"]
        data["ukr_price"] = self.parse_ucr_item_price(int(data["code"]))
        data["image"] = ", ".join(item["imgs"])
        # print(data)
        IkeaItems.insert(**data).on_conflict_ignore().execute()
        return data

    def get_groups(self, items):
        groups = []
        for i in items:
            for t in i["tags"][1:-1]:
                if t not in groups:
                    groups.append(t)

        res = []
        done = []
        for i in items:
            tags = i["tags"][2:-1]
            for k in range(len(tags)):
                t = tags[k]
                if t not in done:
                    res.append({
                        "Название_группы": t,
                        "Идентификатор_группы": groups.index(t),
                        "Идентификатор_родителя": groups.index(tags[k - 1]) if k > 0 else 0
                    })
                    done.append(t)

        self.groups_lists = groups
        return res

    def export_to_db(self):
        items = []
        count = IkeaItems.select().count()
        for i in range(0, count, 300):
            batch = IkeaItems.select().order_by(IkeaItems.id).offset(i).limit(300).execute()
            items += [model_to_dict(b) for b in batch]
        items = list(filter(lambda x: len(set(bad_cats) & set(x["tags"])) == 0, items))
        print(f"Import {len(items)} items")
        groups = self.get_groups(items)

        df = pd.DataFrame.from_dict(groups)
        df.loc[df['Идентификатор_родителя'] == 0, 'Идентификатор_родителя'] = ''

        df2 = pd.DataFrame.from_dict([self.to_shop_format(i) for i in items])

        def preparing(cod):
            cod = str(cod)
            while len(cod) < 8:
                cod = "0" + cod
            return f"{cod[:3]}.{cod[3:6]}.{cod[6:]}"

        df2['Код_товара'] = df2['Код_товара'].apply(lambda x: preparing(x))
        df2.drop_duplicates(subset='Идентификатор_товара', keep="last")
        df2["Идентификатор_группы"] = df2["Идентификатор_группы"].fillna(0).astype('int64')
        df2.loc[df2['Идентификатор_группы'] == 0, 'Идентификатор_группы'] = ''
        df2 = df2.fillna("")
        df2 = df2.drop_duplicates(subset="Идентификатор_товара")

        df2.to_csv('Export Products Sheet.csv', index=False)
        df.to_csv('Export Groups Sheet.csv', index=False)

        from pyexcel import merge_all_to_a_book
        merge_all_to_a_book(['Export Products Sheet.csv', 'Export Groups Sheet.csv'], "output.xlsx")

        import openpyxl
        wb = openpyxl.load_workbook("output.xlsx")
        for sheet in wb:
            sheet_name = sheet.title
            sheet.title = sheet_name.replace(".csv", "")
        wb.save("output.xlsx")
