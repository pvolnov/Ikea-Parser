import telebot

from app.logging_config import logger
from app.representers.represent_data_utils import *
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_PASS, MessageStatus

from app.models import IkeaItems, Tasks, TgUsers

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


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


# @bot.message_handler(content_types=['document'])
# def new_doc(message):
#     # save file
#     user = TgUsers.get_or_none(TgUsers.tel_id == message.chat.id)
#     if user is None:
#         bot.send_message(message.chat.id, "Пройдите авторизацию")
#         return
#     file_info = bot.get_file(message.document.file_id)
#     downloaded_file = bot.download_file(file_info.file_path)
#     with open("../.tmp/file.xlsx", "wb") as f:
#         f.write(downloaded_file)
#     doc = pd.read_excel('file.xlsx').fillna("").to_dict('records')
#     bot.reply_to(message, f"Загружен файл ({len(doc)} строк)")
#
#     if user.mst == MessageStatus.DIFFERENCE:
#         codes = []
#         for d in doc:
#             if d['Производитель'] == "IKEA":
#                 codes.append(d['Код_товара'].replace(".", "").strip("0"))
#         get_ua_items(set(codes))
#         with open("output.xlsx", "rb") as f:
#             bot.send_document(message.chat.id, f, caption="Остаточные данные с ikea.ua")
#
#     if user.mst == MessageStatus.LOAD_FROM_IKEA_1:
#         avilable_code = IkeaItems.select(IkeaItems.code).execute()
#         avilable_code = set([i.code for i in avilable_code])
#         print("New doc")
#
#         for d in doc:
#             if d['Производитель'] == "IKEA":
#                 code = d['Код_товара'].replace(".", "").strip("0")
#                 if int(code) not in avilable_code:
#                     d['Наличие'] = "-"
#
#         df = pd.DataFrame.from_dict(doc)
#         df["Идентификатор_товара"] = df["Код_товара"].apply(lambda x: x.replace(".", "").strip("0"))
#         df["Валюта"] = "UAH"
#         df.to_excel("res.xlsx", index=False)
#         print("Файл подготовлен")
#         with open("res.xlsx", "rb") as f:
#             bot.send_document(message.chat.id, f, caption="Данные с заполненной колонкой наличия")
#
#     elif user.mst in [MessageStatus.UPDATE_UA, MessageStatus.UPDATE_PL]:
#         mode = "PL" if user.mst == MessageStatus.UPDATE_PL else "UA"
#         print("Updating with mode: %s" % mode)
#         bot.send_message(message.chat.id, f"В файле {len(doc)} товаров")
#         if mode == "UA":
#             items = UaIkeaItems.select().execute()
#             PRICES_TABLE = PRICES
#         else:
#             items = PlIkeaItems.select().execute()
#             PRICES_TABLE = PRICES_PL
#
#         items = {i.code: {
#             "price": float(str(i.data["Цена"]).replace(" ", "")),
#             "avilable": i.avilable,
#         } for i in items}
#
#         for dat in tqdm(doc):
#             code = re.sub(r"\D+", "", dat['Код_товара']).strip("0")
#             if code in items:
#                 dat['Наличие'] = "+" if items[code]["avilable"] else "-"
#
#                 for p in PRICES_TABLE:
#                     if p > items[code]["price"]:
#                         dat['Цена'] = int(items[code]["price"] * PRICES_TABLE[p])
#                         break
#             else:
#                 dat['Наличие'] = "-"
#                 dat['Цена'] = 0
#
#         pd.DataFrame.from_dict(doc).to_excel("res.xlsx", index=False)
#         with open("res.xlsx", "rb") as f:
#             bot.send_document(message.chat.id, f, caption="Данные с ikea.ua с заполненной колонкой наличия")


@bot.message_handler(content_types=["text"])
def text_mes(message):
    print(message.text)
    if message.text == TELEGRAM_BOT_PASS:
        TgUsers.get_or_create(tel_id=message.chat.id)
        bot.send_message(message.chat.id, "Бот активирован", reply_markup=parsels_keyboard)
        return

    u = TgUsers.get_or_none(TgUsers.tel_id == message.chat.id)
    if u is None:
        bot.send_message(message.chat.id, "Бот не активирован")
        return

    if message.text in [MessageStatus.LOAD_FROM_IKEA_1, MessageStatus.LOAD_FROM_IKEA_2,
                        MessageStatus.LOAD_FROM_IKEA_3, MessageStatus.LOAD_FROM_IKEA_4,
                        MessageStatus.LOAD_FROM_IKEA_5]:
        u.mst = MessageStatus.LOAD_FROM_IKEA_1
        bot.send_message(u.tel_id, "Пришлите файл для обновления информации о наличии товаров")

    elif message.text == MessageStatus.UPDATE_GOOGLE_TREKING:
        n = update_delivery()
        bot.send_message(u.tel_id, f"Список посылок обновлен, всего {n} посылок")
    elif message.text == MessageStatus.UPDATE_GOOGLE_SHEETS:
        update_google_sheets()
        bot.send_message(u.tel_id, "Таблица обновлена")

    elif message.text == MessageStatus.DIFFERENCE:
        u.mst = MessageStatus.DIFFERENCE
        bot.send_message(u.tel_id, "Пришлите файл для которого нужно уточнить разницу")

    elif message.text in [MessageStatus.DATA_FROM_IKEA_UA, MessageStatus.DATA_FROM_IKEA_PL]:
        filename = PROJECT_DIR + '/data/output.xlsx'
        bot.send_message(message.chat.id, "Начали готовить файлы, подождите пару минут")
        mode= ''
        if message.text == MessageStatus.DATA_FROM_IKEA_UA:
            # save_ikea_product_to_csv(country="UA", filename=filename)
            mode = 'UA'
        else:
            mode = 'PL'
            # save_ikea_product_to_csv(country="PL", filename=filename)
        get_ua_items(mode=mode)

        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption="Актуальные данные с ikea " + mode)

    elif message.text in [MessageStatus.UPDATE_UA, MessageStatus.UPDATE_PL]:
        u.mst = message.text
        bot.send_message(message.chat.id, "Пришлите файл .xlsx с обязательной колонкой `Код_товара`")
    else:
        bot.send_message(message.chat.id, "Я не отвечаю на сообщения", reply_markup=parsels_keyboard)
        return

    u.save()


def start_pooling():
    logger.info("Start bot pulling")
    bot.polling(none_stop=True, timeout=60)


if __name__ == "__main__":
    import os
    start_pooling()
