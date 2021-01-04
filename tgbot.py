from __future__ import print_function

import json
import os.path
import os.path as op
import pickle
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.policy import SMTPUTF8

import pandas as pd
import requests
import telebot
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyexcel import merge_all_to_a_book
from telebot import types
from tqdm import tqdm

from bot.models import IkeaItems, Tasks, TgUsers, UaIkeaItems, PlIkeaItems

PRICES = {
    10: 1.5,
    20: 1.45,
    100: 1.40,
    200: 1.35,
    3000: 1.30,
    5000: 1.29,
    10000: 1.27,
    100000: 1.25,
}

PRICES_PL = {
    10: 12,
    20: 11.8,
    50: 11.5,
    100: 11.25,
    200: 11,
    500: 10.5,
    10000: 10,
    100000: 9.8,
}

TB_BOT_TOKEN = "1379071918:AAFkcIhIbi3YmRpS4bRApoefFi3YbzOmlpk"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1OQstaXj8e7wWv4-VM-uArPW0rE32kj_Eak056WnVDXg'
SAMPLE_RANGE_NAME = 'Лист1!A2:A30000'

bot = telebot.TeleBot(TB_BOT_TOKEN)

with open("search_text.pk", "rb") as f:
    SEARCH_TEXT = pickle.load(f)


class MesssageStatus:
    LOAD_FROM_IKEA_1 = "PLsalre"
    LOAD_FROM_IKEA_2 = "Tovarnyak"
    LOAD_FROM_IKEA_3 = "Orgodom"
    LOAD_FROM_IKEA_4 = "Markett"
    LOAD_FROM_IKEA_5 = "DomComfort"
    UPDATE_GOOGLE_SHEETS = "Update google table Ⓖ"
    UPDATE_GOOGLE_TREKING = "Treking update 🧳"
    DIFFERENCE = "Difference 📏"
    UPDATE_UA = "Наличие в ikea.ua 🗳"
    UPDATE_PL = "Наличие в ikea.pl 🗳"
    DATA_FROM_IKEA_UA = "Слепок всей ikea.ua 📥"
    DATA_FROM_IKEA_PL = "Слепок всей ikea.pl 📥"


parsels_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=False,
                                             row_width=2)
parsels_keyboard.add(
    types.KeyboardButton(text=MesssageStatus.LOAD_FROM_IKEA_2),
    types.KeyboardButton(text=MesssageStatus.LOAD_FROM_IKEA_3),
    types.KeyboardButton(text=MesssageStatus.UPDATE_GOOGLE_SHEETS),
    types.KeyboardButton(text=MesssageStatus.UPDATE_GOOGLE_TREKING),
    types.KeyboardButton(text=MesssageStatus.DIFFERENCE),
    types.KeyboardButton(text=MesssageStatus.UPDATE_UA),
    types.KeyboardButton(text=MesssageStatus.UPDATE_PL),
)

parsels_keyboard.add(
    types.KeyboardButton(text=MesssageStatus.DATA_FROM_IKEA_PL),
    types.KeyboardButton(text=MesssageStatus.DATA_FROM_IKEA_UA))


def get_url_cost(code: str):
    r = requests.get("http://sik.search.blue.cdtapps.com/ua/uk/search-result-page", params={
        "q": code
    })
    res = r.json()['searchResultPage']['productWindow']
    if len(res) == 0:
        return None, None
    return res[0]['pipUrl'], res[0]['priceNumeral']


def update_delivery():
    import gspread
    import requests
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd

    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'ikeaparses-google.json', scope)
    client = gspread.authorize(credentials)

    spreadsheet = client.open('Доставка_Ikea')

    r = requests.post("http://testapi.novaposhta.ua/v2.0/en/json/getDocumentList/", data=json.dumps({
        "apiKey": "cdff5758a96e79dc6b5e5a66776ad9fd",
        "modelName": "InternetDocument",
        "calledMethod": "getDocumentList",
    }), headers={
        "Content-Type": "application/json"
    })
    if "data" not in r.json():
        return "Превышено число запросов в минуту"
    req = [{
        "DocumentNumber": d["IntDocNumber"],
        "Phone": d["RecipientsPhone"],
    } for d in r.json()["data"]]

    r = requests.post("http://testapi.novaposhta.ua/v2.0/en/json/getDocumentList/", data=json.dumps({
        "apiKey": "cdff5758a96e79dc6b5e5a66776ad9fd",
        "modelName": "TrackingDocument",
        "calledMethod": "getStatusDocuments",
        "methodProperties": {
            "Documents": req
        }

    }), headers={
        "Content-Type": "application/json"
    })

    doc = pd.DataFrame.from_dict(r.json()["data"])
    doc["Packaging"] = doc["Packaging"].apply(lambda x: "\n".join(c["Description"] for c in x))

    for_drop = ["StatusCode", "LoyaltyCardSender", "MarketplacePartnerToken"]
    doc = doc.drop(columns=[x for x in doc.columns if x in for_drop])
    doc = doc.drop(columns=[x for x in doc.columns if "Ref" in x])
    from config import DEV_STATUS_TRANS
    doc = doc.rename(columns=DEV_STATUS_TRANS)
    doc.to_csv("data.csv")

    with open('data.csv', 'r') as file_obj:
        content = file_obj.read().encode('utf-8')
        client.import_csv(spreadsheet.id, data=content)

    return len(doc)


def update_google_sheets():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    codes = []
    for row in values:
        codes.append(row[0].replace(".", "").strip("0"))
    items = UaIkeaItems.select(UaIkeaItems.code, UaIkeaItems.avilable, UaIkeaItems.data).where(
        UaIkeaItems.code.in_(codes)).execute()
    items = {i.code: i for i in items}
    res = []
    for code in codes:
        if code in items:
            res.append(10 if items[code].avilable else 0)
        else:
            res.append(0)

    service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Лист1!D2:D10000",
        valueInputOption='RAW', body={
            'values': [[r] for r in res],
        }).execute()

    res = []
    for code in codes:
        if code in items:
            pr = float(str(items[code].data["Цена"]).replace(" ", ""))
            for p in PRICES:
                if p > pr:
                    res.append(round(pr * PRICES[p], 2))
                    break
        else:
            res.append(-1)
    service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Лист1!E2:E10000",
        valueInputOption='RAW', body={
            'values': [[r] for r in res],
        }).execute()


def get_ua_items(ignore_codes=[], mode="UA"):
    def get_groups(items):
        groups = []
        for i in items:
            if len(i.tags) > 2:
                for t in i.tags:
                    groups.append(t)
        groups = list(set(groups))

        res = []
        done = []

        for i in items:
            tags_orig = []
            for t in i.tags:
                if t not in tags_orig and t != "":
                    tags_orig.append(t)
            if len(tags_orig) > 2:
                if tags_orig[-2] not in done:
                    res.append({
                        # "Номер_группы": groups.index(i.tags[-2]),
                        "Идентификатор_группы": groups.index(tags_orig[-2]),
                        "Название_группы": tags_orig[-2],
                        # "Номер_родителя": groups.index(i.tags[-3]),
                        "Идентификатор_родителя": groups.index(tags_orig[-3]),
                    })
                    done.append(tags_orig[-2])

                if tags_orig[-3] not in done:
                    res.append({
                        # "Номер_группы": groups.index(i.tags[-3]),
                        "Идентификатор_группы": groups.index(tags_orig[-3]),
                        "Название_группы": tags_orig[-3],
                        # "Номер_родителя": "",
                        "Идентификатор_родителя": "",
                    })
                    done.append(tags_orig[-3])

        return res, groups

    if mode == "UA":
        items = UaIkeaItems.select().execute()
    else:
        items = PlIkeaItems.select().execute()

    groups, groups_lists = get_groups(items)
    df1 = pd.DataFrame.from_dict(groups)

    result = []
    for i in items:
        if i.code.replace(".", "").strip("0") in ignore_codes:
            continue
        if len(i.tags) > 2:
            result.append({
                **i.data,
                "Идентификатор_группы": groups_lists.index(i.tags[-2]),
            })

    all_tasks = {i.code: i for i in items}

    for item in result:
        if item["Код_товара"] in all_tasks:
            item['Наличие'] = "+" if all_tasks[item["Код_товара"]].avilable else "-"
        else:
            item['Наличие'] = "-"

        pr = float(str(item["Цена"]).replace(" ", ""))
        if mode == "UA":
            for p in PRICES:
                if p > pr:
                    item['Цена'] = pr * PRICES[p]
                    break
        else:
            for p, val in PRICES_PL.items():
                if p > pr:
                    item['Цена'] = pr * val
                    break
            print(item['Цена'], pr)

        def preparing(cod):
            cod = str(cod)
            while len(cod) < 8:
                cod = "0" + cod
            return f"{cod[:3]}.{cod[3:6]}.{cod[6:]}"

        if item["Код_товара"] in SEARCH_TEXT:
            item["Ключевые_слова"] = SEARCH_TEXT[item["Код_товара"]]
        else:
            item["Ключевые_слова"] = ",".join(filter(lambda x: len(x) > 3 and not re.search("\d{2,}", x),
                                                     item["Название_позиции"].lower().split(" ")))

        item["Идентификатор_товара"] = item['Код_товара']
        item["Код_товара"] = preparing(item['Код_товара'])
        item["Валюта"] = "UAH"
        item["Цена"] = float(str(item["Цена"]).replace(" ", "").replace(",", "."))

        item["Название_позиции"] = item["Название_позиции"][:100]
        item["Ссылка_изображения"] = ", ".join(item["Ссылка_изображения"].split(", ")[:9])
        if "Примечание" in item:
            del item["Примечание"]

    df1.to_csv('Export Groups Sheet.csv', index=False)
    pd.DataFrame.from_dict(result).to_csv('Export Products Sheet.csv', index=False)

    merge_all_to_a_book(['Export Products Sheet.csv', 'Export Groups Sheet.csv'], "output.xlsx")

    import openpyxl
    wb = openpyxl.load_workbook("output.xlsx")
    for sheet in wb:
        sheet_name = sheet.title
        sheet.title = sheet_name.replace(".csv", "")
    wb.save("output.xlsx")

    return result


@bot.message_handler(commands=['start', 'status'])
def start(message):
    if message.text == "/start":
        bot.send_message(message.chat.id, "Пришлите пароль для активации бота")
    if message.text == "/status":
        n = IkeaItems.select().count()
        empty = IkeaItems.select().where(IkeaItems.avilable == "e").count()
        n2 = Tasks.select().where(Tasks.loaded == True).count()
        n3 = Tasks.select().where(Tasks.updted == True).count()
        n4 = Tasks.select().count()

        mes = f"Items: {n}\n" \
              f"Items empty: {empty}\n" \
              f"For loading: {n2}/{n4} - {n2 / n4 * 100:.2f}%\n" \
              f"Updating: {n3}/{n4} - {n3 / n4 * 100:.2f}%\n"
        bot.send_message(message.chat.id, mes)


def send_mail(email, file, body="", subject="Ikea Bot Data"):
    login = "no-reply@neafiol.site"
    password = "adminnef44!"

    msg = MIMEMultipart(policy=SMTPUTF8)
    msg['From'] = login
    msg['To'] = email
    msg['Subject'] = subject

    part = MIMEBase('application', "octet-stream")
    part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="{}"'.format(op.basename("Data.xlsx")))
    msg.attach(part)

    server = smtplib.SMTP('smtp.yandex.com', 587)
    server.starttls()
    server.login(login, password)
    server.send_message(msg)
    server.quit()


@bot.message_handler(content_types=['document'])
def new_doc(message):
    # save file
    user = TgUsers.get_or_none(TgUsers.tel_id == message.chat.id)
    if user is None:
        bot.send_message(message.chat.id, "Пройдите авторизацию")
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("file.xlsx", "wb") as f:
        f.write(downloaded_file)
    doc = pd.read_excel('file.xlsx').fillna("").to_dict('records')
    bot.reply_to(message, f"Загружен файл ({len(doc)} строк)")

    if user.mst == MesssageStatus.DIFFERENCE:
        codes = []
        for d in doc:
            if d['Производитель'] == "IKEA":
                codes.append(d['Код_товара'].replace(".", "").strip("0"))
        get_ua_items(set(codes))
        with open("output.xlsx", "rb") as f:
            bot.send_document(message.chat.id, f, caption="Остаточные данные с ikea.ua")

    if user.mst == MesssageStatus.LOAD_FROM_IKEA_1:
        avilable_code = IkeaItems.select(IkeaItems.code).execute()
        avilable_code = set([i.code for i in avilable_code])
        print("New doc")

        for d in doc:
            if d['Производитель'] == "IKEA":
                code = d['Код_товара'].replace(".", "").strip("0")
                if int(code) not in avilable_code:
                    d['Наличие'] = "-"

        df = pd.DataFrame.from_dict(doc)
        df["Идентификатор_товара"] = df["Код_товара"].apply(lambda x: x.replace(".", "").strip("0"))
        df["Валюта"] = "UAH"
        df.to_excel("res.xlsx", index=False)
        print("Файл подготовлен")
        with open("res.xlsx", "rb") as f:
            bot.send_document(message.chat.id, f, caption="Данные с заполненной колонкой наличия")

    elif user.mst in [MesssageStatus.UPDATE_UA, MesssageStatus.UPDATE_PL]:
        mode = "PL" if user.mst == MesssageStatus.UPDATE_PL else "UA"
        print("Updating with mode: %s" % mode)
        bot.send_message(message.chat.id, f"В файле {len(doc)} товаров")
        if mode == "UA":
            items = UaIkeaItems.select().execute()
            PRICES_TABLE = PRICES
        else:
            items = PlIkeaItems.select().execute()
            PRICES_TABLE = PRICES_PL

        items = {i.code: {
            "price": float(str(i.data["Цена"]).replace(" ", "")),
            "avilable": i.avilable,
        } for i in items}

        for dat in tqdm(doc):
            code = re.sub(r"\D+", "", dat['Код_товара']).strip("0")
            if code in items:
                dat['Наличие'] = "+" if items[code]["avilable"] else "-"

                for p in PRICES_TABLE:
                    if p > items[code]["price"]:
                        dat['Цена'] = int(items[code]["price"] * PRICES_TABLE[p])
                        break
            else:
                dat['Наличие'] = "-"
                dat['Цена'] = 0

        pd.DataFrame.from_dict(doc).to_excel("res.xlsx", index=False)
        with open("res.xlsx", "rb") as f:
            bot.send_document(message.chat.id, f, caption="Данные с ikea.ua с заполненной колонкой наличия")


@bot.message_handler(content_types=["text"])
def text_mes(message):
    print(message.text)
    if message.text == "admin4t":
        TgUsers.get_or_create(tel_id=message.chat.id)
        bot.send_message(message.chat.id, "Бот активирован", reply_markup=parsels_keyboard)
        return

    u = TgUsers.get_or_none(TgUsers.tel_id == message.chat.id)
    if u is None:
        bot.send_message(message.chat.id, "Бот не активирован")
        return

    if message.text in [MesssageStatus.LOAD_FROM_IKEA_1, MesssageStatus.LOAD_FROM_IKEA_2,
                        MesssageStatus.LOAD_FROM_IKEA_3, MesssageStatus.LOAD_FROM_IKEA_4,
                        MesssageStatus.LOAD_FROM_IKEA_5]:
        u.mst = MesssageStatus.LOAD_FROM_IKEA_1
        bot.send_message(u.tel_id, "Пришлите файл для обновления информации о наличии товаров")

    elif message.text == MesssageStatus.UPDATE_GOOGLE_TREKING:
        n = update_delivery()
        bot.send_message(u.tel_id, f"Список посылок обновлен, всего {n} посылок")
    elif message.text == MesssageStatus.UPDATE_GOOGLE_SHEETS:
        update_google_sheets()
        bot.send_message(u.tel_id, "Таблица обновлена")

    elif message.text == MesssageStatus.DIFFERENCE:
        u.mst = MesssageStatus.DIFFERENCE
        bot.send_message(u.tel_id, "Пришлите файл для которого нужно уточнить разницу")

    elif message.text in [MesssageStatus.DATA_FROM_IKEA_UA, MesssageStatus.DATA_FROM_IKEA_PL]:
        bot.send_message(message.chat.id, "Начали готовить файлы, подождите пару минут")
        if message.text == MesssageStatus.DATA_FROM_IKEA_UA:
            get_ua_items(mode="UA")
        else:
            get_ua_items(mode="PL")

        with open("output.xlsx", "rb") as f:
            bot.send_document(message.chat.id, f, caption="Актуальные данные с ikea.ua")

    elif message.text in [MesssageStatus.UPDATE_UA, MesssageStatus.UPDATE_PL]:
        u.mst = message.text
        bot.send_message(message.chat.id, "Пришлите файл .xlsx с обязательной колонкой `Код_товара`")
    else:
        bot.send_message(message.chat.id, "Я не отвечаю на сообщения")
        return

    u.save()


if __name__ == "__main__":
    print("Start")
    bot.polling(none_stop=True, timeout=60)
