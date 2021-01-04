import os.path as op
import re
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.policy import SMTPUTF8

import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

from bot.models import Tasks, IkeaItems
from bot.parser import Parser
from bot.translate import Translate


def send_mail(email, body="", subject="Ikea Data"):
    login = "no-reply@neafiol.site"
    password = "adminnef44!"

    msg = MIMEMultipart(policy=SMTPUTF8)
    msg['From'] = login
    msg['To'] = email
    msg['Subject'] = subject

    part = MIMEBase('application', "octet-stream")
    with open("Export Groups Sheet.xlsx", 'rb') as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="{}"'.format(op.basename("Export Groups Sheet.xlsx")))
    msg.attach(part)

    part = MIMEBase('application', "octet-stream")
    with open("Export Products Sheet.xlsx", 'rb') as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="{}"'.format(op.basename("Export Products Sheet.xlsx")))
    msg.attach(part)

    server = smtplib.SMTP('smtp.yandex.com', 587)
    server.starttls()
    server.login(login, password)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    print("RUN V.2")

    i = Parser().parse_item("https://www.ikea.com/pl/pl/p/duvholmen-poduszka-wew-poduszki-oparcia-zewnetrzne-szary-10391833/")

    print(i)

    while False:
        # try:
        #     driver = webdriver.Remote(
        #         command_executor='http://127.0.0.1:4444/wd/hub',
        #         desired_capabilities=DesiredCapabilities.FIREFOX)

            driver = webdriver.Firefox()

            p = Parser(driver, server_url="http://127.0.0.1:4444/wd/hub")

            if Tasks.select().where(Tasks.updted == False).count() == 0:
                items = p.update_items_tasks()
                print("*" * 15 + f"Total find {len(items)} items" + "*" * 15)
            else:
                print("Continue updating")

            n = Tasks.select().where(Tasks.loaded == False).count()
            print(f"Need load {n} items")
            print("=====================")
            time.sleep(10)
            while True:  # !!!!!!!!
                # try:
                for_loading = Tasks.select().where(Tasks.loaded == False).limit(10).execute()
                for_loading = [f.url for f in for_loading]
                for url in for_loading:
                    i = p.parse_item("https://www.ikea.com/pl/pl/p/duvholmen-poduszka-wew-poduszki-oparcia-zewnetrzne-szary-10391833/")
                    if i is None:
                        continue
                    i["id"] = re.search(r"\d+", url).group(0)
                    i["url"] = url
                    i["discr"] = re.sub("\d+\.\d+\.\d+", "", i["discr"])
                    i["details"] = re.sub("\d+\.\d+\.\d+", "", i["details"])
                    p.save_to_db(i)
                    print(f"Complete: {url}")

                n = Tasks.update({Tasks.loaded: True}).where(Tasks.url.in_(for_loading)).execute()
                print(n)

                if len(for_loading) < 10:
                    break
                print("=" * 70)

            print("Loading comlete")
            while True:
                try:
                    for_loading = Tasks.select().where(Tasks.updted == False).limit(10).execute()
                    for f in for_loading:
                        avilable = p.update_available(f.url)
                        IkeaItems.update({IkeaItems.avilable: avilable}).where(IkeaItems.url == f.url).execute()
                        print(f.url, avilable)

                    for_loading = [f.url for f in for_loading]
                    Tasks.update({Tasks.updted: True}).where(Tasks.url.in_(for_loading)).execute()
                    if len(for_loading) < 10:
                        break
                except Exception as e:
                    p.modal_accept = False
                    print(e)
                    time.sleep(3)

            IkeaItems.update({IkeaItems.new: False}).execute()
            Tasks.update({Tasks.updted: False}).execute()

            print("Update compliting...")

        # except Exception as e:
        #     time.sleep(5)
        #     print("Error", e)
        #     requests.get(f"https://alarmerbot.ru/?key=df548f-61ac83-624ea4&message=Ikea error {e}")
