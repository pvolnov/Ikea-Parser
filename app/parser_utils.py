import re
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from app.models import UaIkeaItems
from app.logging_config import logger


class ParserUtils:
    """
    Файл с различным утилитами для парсинга икеи
    Класс ParserUtils используется другими модулями для совершения работы,
    тут находятся чистые функции
    """

    @staticmethod
    def get_items_links(driver, url):
        """
        url should be like "https://www.ikea.com/pl/pl/cat/tovari-products/"
        """
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html5lib')
        urls = soup.find_all("a", {"class": "vn-link vn-nav__link"})
        uitems = []
        done = []

        for u in tqdm(urls):
            if u['href'] in done:
                continue
            driver.get(u['href'] + "?page=20")
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html5lib')
            uitems += [u['href'] for u in soup.find_all("a", {"aria-label": True})]
            done.append(u['href'])

        uitems = list(filter(lambda x: "/p/" in x, set(uitems)))
        logger.info("Find: %s items", len(uitems))

        return [{
            "url": u,
            "code": re.search(r"\d+", u.split("-")[-1]).group(0).strip("0")
        } for u in uitems]

    @staticmethod
    def parse_ikea_page(url):
        data = {
            "Тип_товара": "r",
            "Валюта": "UAH",
            "Примечание": "UAH",
            "Единица_измерения": "шт"
        }

        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html5lib')

        data["Код_товара"] = re.search(r"\d+", url.split("-")[-1]).group(0)

        data["Описание"] = soup.find("meta", {"name": "description"})["content"]
        data["Название_позиции"] = data["Описание"].split(".")[0]
        data["Поисковые_запросы"] = soup.find("meta", {"name": "keywords"})["content"]
        data["Цена"] = soup.find("div", {"data-product-price": True})["data-product-price"]
        images = [i['src'] for i in soup.find_all("img", {"class": "range-revamp-aspect-ratio-image__image"})]
        data["Ссылка_изображения"] = ", ".join(images[:9])

        details = ""

        if soup.dl:
            for p in soup.find("dl").find_all("div"):
                details += p.dt.text.replace("\xa0", "") + " " + p.dd.text + "\n"
        else:
            for p in soup.find_all("span", {"class": "range-revamp-product-details__label"}):
                details += p.text.replace("\n", "").replace("  ", "") + "\n"

        data["Описание"] += "\n" + details
        if soup.find("div", {"id": "SEC_product-details-material-and-care"}):
            data["Описание"] += "\n" + "\n".join(
                [d.text for d in soup.find("div", {"id": "SEC_product-details-material-and-care"}).find_all("div")])

        tags = [l.span.text for l in soup.find_all("li", {"class": "bc-breadcrumb__list-item"})]
        return data, tags

    @staticmethod
    def check_avil(driver, urls):
        driver.delete_all_cookies()
        driver.refresh()

        items = {}

        for url in urls:
            code = re.findall(r"\d+", url)[-1].strip("0")
            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html5lib')
            price = 0
            if soup.find("div", {"data-product-price": True}):
                price = soup.find("div", {"data-product-price": True})["data-product-price"]
            items[code] = {
                "price": price,
                "Личные_заметки": "",
                "avilable": False
            }

            for k in range(4):
                try:
                    driver.find_element_by_class_name("range-revamp-btn--emphasised").click()
                    time.sleep(3)
                    soup = BeautifulSoup(driver.page_source, 'html5lib')
                    if soup.find("div", {"data-product-price": True}):
                        items[code]["price"] = soup.find("div", {"data-product-price": True})["data-product-price"]

                    if soup.find("h3", {"class": "range-revamp-popup__heading"}) and "Ой!" in soup.find("h3", {
                        "class": "range-revamp-popup__heading"}).text:

                        items[code]["avilable"] = False
                        items[code]["Личные_заметки"] = "Ошибка при добавлении в корзину"
                    else:
                        items[code]["avilable"] = True

                    if "30373588" == str(code):
                        driver.save_screenshot(f"30373588.png")

                    break
                except:
                    time.sleep(0.5)
        return items

    @staticmethod
    def check_avil_in_lublin(driver, url):
        driver.get(url)
        for t in range(5):
            time.sleep(0.3)
            try:
                driver.find_element_by_xpath(
                    "//a[@class='range-revamp-stockcheck__available-for-delivery-link link']").click()
            except:
                continue

            soup = BeautifulSoup(driver.page_source, 'html5lib')

            if soup.find("div", {"data-product-price": True}):
                price = soup.find("div", {"data-product-price": True})["data-product-price"]
            else:
                price = 0
            itm = UaIkeaItems.get_or_none(UaIkeaItems.url == url)
            if itm and price:
                itm.data["Цена"] = price
                itm.save()

            for div in soup.find_all("div", {"class": "range-revamp-change-store__store"}):
                if "Lublin" in div.text and "Dostępny" in div.text:
                    return True
        return False
