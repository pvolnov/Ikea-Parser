
# DB settings
DB_NAME = 'ikea'
DB_USER = 'postgres'
DB_PASSWORD = 'nef441'
DB_HOST = 'sw.neafiol.site'
SB_PORT = 5432

# -----------------------------------------------
# Logging settings
ALARMER_BOT_KEY = "104839-00cc49-791ee0"
FORMAT = '%(funcName)s %(levelname)s: %(message)s'
TG_FORMAT = 'PARSER %(levelname)s: %(message)s'

# -----------------------------------------------
client_id = "403903445695-juercfio7dt7d1vpnqv4iihpk1fv8dgi.apps.googleusercontent.com"
client_secret = "OT56q_gN4U5wcoVck1jk9nB_"

DEV_STATUS_TRANS = {'Number': 'Номер ЭН', 'Redelivery': 'Идентификатор обратной доставки. 0 - нет ОД 1 - есть ОД',
                    'RedeliverySum': 'Сумма обратной доставки',
                    'RedeliveryNum': 'Идентификатор нора ЭН обратной доствки',
                    'RedeliveryPayer': 'Идентификатор плательщика обратной доставки',
                    'OwnerDocumentType': 'Тип ЭН на основании',
                    'LastCreatedOnTheBasisDocumentType': 'Последние изменения, тип документа',
                    'LastCreatedOnTheBasisPayerType': 'Последние изменения, тип плательщика',
                    'LastCreatedOnTheBasisDateTime': 'Последние изменения, дата создания',
                    'LastTransactionStatusGM': 'Последний статус транзакции денежного перевода',
                    'LastTransactionDateTimeGM': 'Последнее время и дата транзакции денежного перевода',
                    'DateCreated': 'Дата создания ЭН', 'DocumentWeight': 'Вес',
                    'CheckWeight': 'Информация после контрольного взвешивания', 'DocumentCost': 'Стоимость доставки',
                    'SumBeforeCheckWeight': 'Информация до контрольного взвешивания',
                    'PayerType': 'Идентификатор плательщика',
                    'RecipientFullName': 'Данные ФИО получателя с накладной (при вводе телефона)',
                    'RecipientDateTime': 'Дата, когда груз забрал получатель',
                    'ScheduledDeliveryDate': 'Ожидаемая дата доставки', 'PaymentMethod': 'Способ оплаты',
                    'CargoDescriptionString': 'Описание посылки', 'CargoType': 'Тип груза',
                    'CitySender': 'Город отправителя', 'CityRecipient': 'Город получателя',
                    'WarehouseRecipient': 'Склад получателя', 'CounterpartyType': 'Идентификатор',
                    'AfterpaymentOnGoodsCost': 'Контроль Оплаты', 'ServiceType': 'Идентификатор способа доставки',
                    'UndeliveryReasonsSubtypeDescription': 'Описание причины неразвоза',
                    'WarehouseRecipientNumber': 'Номер отделения получателя',
                    'LastCreatedOnTheBasisNumber': 'Последние изменения, номер ЭН',
                    'PhoneRecipient': 'Телефон получателя',
                    'RecipientFullNameEW': 'Данные ФИО получателя с накладной (при вводе телефона)',
                    'WarehouseRecipientInternetAddressRef': 'Идентификатор склада получателя',
                    'MarketplacePartnerToken': '', 'ClientBarcode': 'Внутренний номер заказа',
                    'RecipientAddress': 'Адрес получателя',
                    'CounterpartyRecipientDescription': 'Описание контрагента получателя',
                    'CounterpartySenderType': 'Тип контрагента отправителя',
                    'DateScan': 'Дата сканировки, которая привела к формированию статуса',
                    'PaymentStatus': 'Статус для интернет эквайринг',
                    'PaymentStatusDate': 'Дата оплаты для интернет эквайринг',
                    'AmountToPay': 'Сумма к оплате для интернет эквайринг',
                    'AmountPaid': 'Оплачено для интернет эквайринг', 'Status': 'Статус',
                    'StatusCode': 'Идентификатор статуса',
                    'RefEW': 'Идентификатор накладной для эквайринга (используется в рабочих целях)',
                    'BackwardDeliverySubTypesActions': 'Информация по не стандартным подтипам обратной доставки',
                    'BackwardDeliverySubTypesServices': 'Информация по не стандартным подтипам обратной доставки',
                    'UndeliveryReasons': 'Причина неразвоза', 'DatePayedKeeping': 'Дата начала платного хранения'}
