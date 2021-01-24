"""
TODO: Узнать у Пети что тут происходит, пока не понимаю нафига нужен этот файл
Обращение к API сайта testapi.novaposhta.ua
Сохранение данных в гугл таблички
"""

import json

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

from app.models import Posts
from app.logging_config import logger


scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '../data/ikeaparses-google.json', scope)
client = gspread.authorize(credentials)

spreadsheet = client.open('Доставка_Ikea')

if __name__ == '__main__':
    r = requests.post("http://testapi.novaposhta.ua/v2.0/en/json/getDocumentList/", data=json.dumps({
        "apiKey": "cdff5758a96e79dc6b5e5a66776ad9fd",
        "modelName": "InternetDocument",
        "calledMethod": "getDocumentList",
    }), headers={
        "Content-Type": "application/json"
    })

    req = [{
        "DocumentNumber": d["IntDocNumber"],
        "Phone": d["RecipientsPhone"],
    } for d in r.json()["data"]]

    logger.info('Documents: %s', req)

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

    posts = Posts.select().execute()
    posts = {p.item_id: p.history for p in posts}

    items = []

    for d in r.json()["data"]:
        items.append({
            "item_id": d["Number"],
            "info": d,
            "history": posts.get(int(d["Number"])) + [d["Status"]]
        })

    logger.debug("items found: %s", len(items))
    Posts.delete().execute()
    Posts.insert_many(items).execute()

