import re
import time

from bs4 import BeautifulSoup
from peewee import fn
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from bot.models import UaIkeaItems, PlIkeaItems


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
            except Exception as e:
                # print(e)
                time.sleep(0.5)

    # driver.get("https://checkout.ua.ikea.com/uk/checkout")
    # time.sleep(3)
    # if driver.find_elements_by_id("NewAddress_FirstName"):
    #     print("NewAddress_FirstName")
    #     return items
    #
    # soup = BeautifulSoup(driver.page_source, 'html5lib')
    # if not soup.tbody:
    #     print("Access diend")
    #     return items
    #
    # for item in soup.tbody.find_all("tr"):
    #     if "Кількість" in str(item):
    #         code = item.find("div", {"id": "itemNumber"}
    #                          ).text.replace("Артикул номер: ", "").replace(".", "").strip("0")
    #         items[code]["avilable"] = not item.td.span.input.has_attr("class")
    #         items[code]["Личные_заметки"] = "Проверено в корзине"

    return items


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

        price = soup.find("div", {"data-product-price": True})["data-product-price"]
        itm = UaIkeaItems.get(UaIkeaItems.url == url)
        itm.data["Цена"] = price
        itm.save()

        for div in soup.find_all("div", {"class": "range-revamp-change-store__store"}):
            if "Lublin" in div.text and "Dostępny" in div.text:
                return True
    return False


if __name__ == "__main__":
    print("START")

    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = None
    # driver = webdriver.Firefox()

    n = 0
    while True:

        if driver is None:
            driver = webdriver.Remote(
                command_executor='http://dig.neafiol.site:4444/wd/hub',
                desired_capabilities={
                    "browserName": "chrome",
                    "sessionTimeout": "5m"
                },
                options=chrome_options
            )

        # ================= Pl items update =================

        tasks = PlIkeaItems.select(PlIkeaItems.url, PlIkeaItems.code, PlIkeaItems.id).where(
            PlIkeaItems.avilable_updated == False).order_by(
            fn.Random()).limit(40).execute()

        for t in tasks:
            avil = check_avil_in_lublin(driver, t.url)
            PlIkeaItems.set_by_id(t.id, {"avilable": avil, "avilable_updated": True})
            print(t.url, avil)

        if len(tasks) == 0:
            print("All is loaded")
            PlIkeaItems.update({PlIkeaItems.avilable_updated: False}).execute()
            continue

        # ================= Ua items updates =================

        tasks = UaIkeaItems.select().where(
            UaIkeaItems.avilable_updated == False).order_by(
            fn.Random()).limit(15).execute()

        if len(tasks) == 0:
            print("All is loaded")
            UaIkeaItems.update({UaIkeaItems.avilable_updated: False}).execute()
            continue

        tasks_codes = {t.code.replace(".", "").strip("0"): t for t in tasks}
        urls = [t.url for t in tasks]

        UaIkeaItems.update({UaIkeaItems.avilable_updated: True}).where(  # UaIkeaItems.avilable: False
            UaIkeaItems.id.in_([t.id for t in tasks])).execute()

        items = check_avil(driver, urls)

        print("complete", UaIkeaItems.select().where(UaIkeaItems.avilable_updated == True).count())
        for i, v in items.items():
            tasks_codes[i].avilable = v["avilable"]
            tasks_codes[i].avilable_updated = True
            tasks_codes[i].data["Цена"] = v["price"]
            tasks_codes[i].data["Личные_заметки"] = v["Личные_заметки"]
            tasks_codes[i].save()

        # restart driver
        n += 1

        if n > 50000:
            n = 0
            driver.quit()
            driver = webdriver.Remote(
                command_executor='http://dig.neafiol.site:4444/wd/hub',
                desired_capabilities={
                    "browserName": "chrome",
                    "sessionTimeout": "5m"
                },
                options=chrome_options
            )
