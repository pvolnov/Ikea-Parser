"""
Этот файл (а точнее цикл в main) обновляет доступность товаров в базе дынных
Можно сказать, держит список товаров в актуальном состоянии, проверяет наличие их через сайт икеи
"""

from peewee import fn
from selenium import webdriver
from contextlib import suppress

from app.models import UaIkeaItems, PlIkeaItems
from app.logging_config import logger
from app.ikea_parser.parser_utils import Parser


def update_available_pile():
    parser = Parser()
    logger.info("START UPDATE")

    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = None

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

        try:

            # ================= Pl items update =================

            tasks = PlIkeaItems.select(PlIkeaItems.url, PlIkeaItems.code, PlIkeaItems.id).where(
                PlIkeaItems.avilable_updated == False).order_by(
                fn.Random()).limit(40).execute()

            for t in tasks:
                avil = parser.check_avil_in_lublin(driver, t.url)
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
                logger.info("All tasks loaded")
                UaIkeaItems.update({UaIkeaItems.avilable_updated: False}).execute()
                continue

            tasks_codes = {t.code.replace(".", "").strip("0"): t for t in tasks}
            urls = [t.url for t in tasks]

            UaIkeaItems.update({UaIkeaItems.avilable_updated: True}).where(  # UaIkeaItems.avilable: False
                UaIkeaItems.id.in_([t.id for t in tasks])).execute()

            items = parser.check_avil(driver, urls)

            logger.info("complete %s tasks updating",
                        UaIkeaItems.select().where(UaIkeaItems.avilable_updated == True).count())
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
        except:
            logger.exception('Something go wrong in updates available')

            with suppress(Exception):
                driver.quit()

            driver = None


if __name__ == "__main__":
    update_available_pile()
