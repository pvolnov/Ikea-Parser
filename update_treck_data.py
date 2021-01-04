import json

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

from bot.models import Posts

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

req = [{
    "DocumentNumber": d["IntDocNumber"],
    "Phone": d["RecipientsPhone"],
} for d in r.json()["data"]]
print("Documents", r.json())

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
print(r.json(), req)

for d in r.json()["data"]:
    items.append({
        "item_id": d["Number"],
        "info": d,
        "history": posts.get(int(d["Number"])) + [d["Status"]]
    })

print(len(items))
Posts.delete().execute()
Posts.insert_many(items).execute()
