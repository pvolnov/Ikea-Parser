import re
import requests
from bs4 import BeautifulSoup
from app.logging_config import logger


def get_translate_ikea_club(code):
    r = requests.get(f"https://ikea-club.com.ua/sku-{code}")
    soup = BeautifulSoup(r.text, 'html5lib')
    data = {}
    tags = []
    try:
        discr = ""
        for div in soup.find("div", {"itemprop": "description"}).find_all("div", {"class": "productInformation"})[2:]:
            discr += div.get_text(separator=" ").strip() + "\n"
        data["Описание"] = discr
        data["Примечание"] = "RUS"

        name = soup.find("h1", {"itemprop": "name"}).text.split(",")[0]
        data["Название_позиции"] = re.sub(r"[\n\s]+", " ", name).strip(" ")

        tags = [t.text for t in soup.find_all("span", {"itemprop": "title"})[1:]]
    except:
        logger.exception("Translate not found, code: %s", code)
        return None, None

    return data, tags
