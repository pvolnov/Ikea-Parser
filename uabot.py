import re
import time

import requests
from bs4 import BeautifulSoup
from peewee import EXCLUDED
from selenium import webdriver
from tqdm import tqdm

from bot.models import UaIkeaItems, PlIkeaItems


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


def get_translate_ikea_club(code):
    r = requests.get(f"https://ikea-club.com.ua/sku-{code}")
    soup = BeautifulSoup(r.text, 'html5lib')
    data = {}
    try:
        discr = ""
        for div in soup.find("div", {"itemprop": "description"}).find_all("div", {"class": "productInformation"})[2:]:
            discr += div.get_text(separator=" ").strip() + "\n"
        data["Описание"] = discr
        data["Примечание"] = "RUS"

        name = soup.find("h1", {"itemprop": "name"}).text.split(",")[0]
        data["Название_позиции"] = re.sub(r"[\n\s]+", " ", name).strip(" ")

        tags = [t.text for t in soup.find_all("span", {"itemprop": "title"})[1:]]
    except Exception as e:
        print(code, "Translate not found")
        return None, None

    return data, tags


def get_translate_mtranslator(driver, text):
    time.sleep(0.2)
    driver.find_element_by_id("text").clear()
    driver.find_element_by_id("text").send_keys(text)
    driver.find_element_by_id("go_btn").click()
    while driver.find_element_by_id("text_out").get_attribute("value") == "":
        time.sleep(0.2)
    return driver.find_element_by_id("text_out").get_attribute("value")


def mtranslate(driver, item, tags):
    res = {}
    driver.get(f"https://www.m-translate.ru/translator/text#text=test&direction=pl-ru")
    res["Описание"] = get_translate_mtranslator(driver, item["Описание"])
    res["Название_позиции"] = get_translate_mtranslator(driver, item["Название_позиции"])
    tags2 = []
    for t in tags:
        tags2.append(get_translate_mtranslator(driver, t))
    return res, tags2


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
    # data["subname"] = soup.find("span", {"class": "range-revamp-header-section__description-text"}).text
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


def get_items_links(url="https://www.ikea.com/pl/pl/cat/tovari-products/"):
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
    print("Find:", len(uitems))

    return [{
        "url": u,
        "code": re.search(r"\d+", u.split("-")[-1]).group(0).strip("0")
    } for u in uitems]


if __name__ == "__main__":
    driver = webdriver.Firefox()

    mode = "PL"
    for mode in ["UA", "PL"]:
        print("RUN WITH MODE", mode)

        if mode == "UA":
            uitems = get_items_links("https://www.ikea.com/ua/uk/cat/tovari-products/")
            UaIkeaItems.insert_many(uitems).on_conflict_ignore().execute()
        else:
            uitems = get_items_links("https://www.ikea.com/pl/pl/cat/tovari-products/")
            PlIkeaItems.insert_many(uitems).on_conflict_ignore().execute()

        print("Start saving items", len(uitems))
        print(uitems)

        tasks = []
        codes = []

        if mode == "UA":
            done = UaIkeaItems.select(UaIkeaItems.code).where(UaIkeaItems.loaded == True).execute()
        else:
            done = PlIkeaItems.select(PlIkeaItems.code).where(PlIkeaItems.loaded == True).execute()
        done = [d.code for d in done]

        print("done", len(done))

        for i, item in tqdm(enumerate(uitems), total=len(uitems)):
            print(i)
            u = item["url"]
            code = item["code"]
            codes.append(code)
            if code in done:
                continue

            try:
                item, tags = parse_ikea_page(u)
                print(item)
                if mode == "PL":
                    ni, tags2 = get_translate_ikea_club(code)
                    if ni:
                        tags = tags2
                        item.update(ni)
                    else:
                        item, tags = mtranslate(driver, item, tags)
                        print("mtranslate done", item)
                else:
                    # ni, tagsf = get_translate(item["Код_товара"])
                    # if tagsf:
                    #     item.update(ni)
                    #     item["Примечание"] = "RUB"
                    pass

                item.update(item)

            except Exception as e:
                print(e, u)
                continue

            tasks.append({
                "code": code,
                "data": item,
                "tags": tags,
                "url": u,
                "loaded": True
            })
            if len(tasks) == 20:
                if mode == "UA":
                    UaIkeaItems.insert_many(tasks).on_conflict(conflict_target=[UaIkeaItems.code],
                                                               update={UaIkeaItems.data: EXCLUDED.data,
                                                                       UaIkeaItems.loaded: EXCLUDED.loaded,
                                                                       UaIkeaItems.tags: EXCLUDED.tags}).execute()

                else:
                    PlIkeaItems.insert_many(tasks).on_conflict(conflict_target=[PlIkeaItems.code],
                                                               update={PlIkeaItems.data: EXCLUDED.data,
                                                                       PlIkeaItems.loaded: EXCLUDED.loaded,
                                                                       PlIkeaItems.tags: EXCLUDED.tags}).execute()
                tasks = []

        if mode == "UA":
            UaIkeaItems.insert_many(tasks).on_conflict(conflict_target=[UaIkeaItems.code],
                                                       update={UaIkeaItems.data: EXCLUDED.data,
                                                               UaIkeaItems.loaded: EXCLUDED.loaded,
                                                               UaIkeaItems.tags: EXCLUDED.tags}).execute()
        else:
            PlIkeaItems.insert_many(tasks).on_conflict(conflict_target=[PlIkeaItems.code],
                                                       update={PlIkeaItems.data: EXCLUDED.data,
                                                               PlIkeaItems.loaded: EXCLUDED.loaded,
                                                               PlIkeaItems.tags: EXCLUDED.tags}).execute()

        driver.quit()
        time.sleep(600)
