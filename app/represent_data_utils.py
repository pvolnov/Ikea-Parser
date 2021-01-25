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
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyexcel import merge_all_to_a_book
from telebot import types
from config import MessageStatus
from logging_config import logger


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
    20: 11.6,
    50: 11.1,
    100: 10.8,
    200: 10.8,
    500: 10.8,
    1000: 10.5,
    3000: 10.5,
    5000: 10.5,
    10000: 10.5,
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1OQstaXj8e7wWv4-VM-uArPW0rE32kj_Eak056WnVDXg'
SAMPLE_RANGE_NAME = 'Лист1!A2:A30000'

with open("../data/search_text.pk", "rb") as f:
    SEARCH_TEXT = pickle.load(f)

parsels_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=False,
                                             row_width=2)
parsels_keyboard.add(
    types.KeyboardButton(text=MessageStatus.LOAD_FROM_IKEA_2),
    types.KeyboardButton(text=MessageStatus.LOAD_FROM_IKEA_3),
    types.KeyboardButton(text=MessageStatus.UPDATE_GOOGLE_SHEETS),
    types.KeyboardButton(text=MessageStatus.UPDATE_GOOGLE_TREKING),
    types.KeyboardButton(text=MessageStatus.DIFFERENCE),
    types.KeyboardButton(text=MessageStatus.UPDATE_UA),
    types.KeyboardButton(text=MessageStatus.UPDATE_PL),
)

parsels_keyboard.add(
    types.KeyboardButton(text=MessageStatus.DATA_FROM_IKEA_PL),
    types.KeyboardButton(text=MessageStatus.DATA_FROM_IKEA_UA))


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
        '../data/ikeaparses-google.json', scope)
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

    with open('../data/data.csv', 'r') as file_obj:
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
    if os.path.exists('../data/token.pickle'):
        with open('../data/token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../data/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../data/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    codes = []
    for row in values:
        codes.append(row[0].replace(".", "").strip("0"))
    items = s.query(IkeaProduct.code, IkeaProduct.ru_data).where(
        IkeaProduct.code.in_(codes)).all()
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


from app.db import current_session as s, IkeaProduct
import pyexcel


def save_xlsx(lines, filename):
    keys = sum(map(lambda x: list(x.keys()), lines), [])
    default = {
        key: None
        for key in keys
    }
    lines = [
        {
            **default,
            **line
        }
        for line in lines
    ]
    pyexcel.save_as(records=lines, dest_file_name=filename)


def save_ikea_product_to_csv(country, filename):
    def converter(value):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return ', '.join(value)
        return str(value)

    products = s.query(IkeaProduct).filter(IkeaProduct.country == country, IkeaProduct.ru_data.isnot(None)).order_by(
        IkeaProduct.id.desc()).limit(1000).all()
    lines = []
    for product in products:
        line = {}
        try:
            line.update({
                'Ссылка на товар': product.url,
                'Страна': product.country,
                **product.ru_data
            })
            line = {
                str(key): converter(value)
                for key, value in line.items()
            }
            lines.append(line)
        except:
            print(product)

    save_xlsx(lines, filename)


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
        items = s.query(IkeaProduct).filter(IkeaProduct.country == 'UA').all()
    else:
        items = s.query(IkeaProduct).filter(IkeaProduct.country == 'PL').all()

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
        try:
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
        except:
            logger.exception('Fail to format product')

    df1.to_csv('Export Groups Sheet.csv', index=False)
    pd.DataFrame.from_dict(result).to_csv('../data/Export Products Sheet.csv', index=False)

    merge_all_to_a_book(['Export Products Sheet.csv', 'Export Groups Sheet.csv'], "output.xlsx")

    import openpyxl
    wb = openpyxl.load_workbook("output.xlsx")
    for sheet in wb:
        sheet_name = sheet.title
        sheet.title = sheet_name.replace(".csv", "")
    wb.save("output.xlsx")

    return result


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
