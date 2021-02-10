"""Работа с db. Тут все таблички и настройки базы данных, используется Postgres"""


from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField, JSONField

from app.config import *

db = PostgresqlExtDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD,
                           host=DB_HOST, port=SB_PORT)


class BaseModel(Model):
    class Meta:
        database = db


class IkeaItems(BaseModel):
    code = IntegerField(unique=True)
    url = TextField(unique=True)
    name = TextField(default="")
    search = TextField(default="")
    discr = TextField(default="")
    price = TextField(default="0")
    ukr_price = TextField(default="0")
    avilable = TextField(default="")
    tags = ArrayField(TextField, default=["", ""])
    image = TextField(default="")
    group_id = IntegerField(default=0)
    subgroup_id = IntegerField(default=0)
    new = BooleanField(default=True)
    correct = BooleanField(default=True)


class Tasks(BaseModel):
    url = TextField(unique=True)
    updted = BooleanField(default=False)
    loaded = BooleanField(default=False)


class UaIkeaItems(BaseModel):
    url = TextField()
    code = TextField(default="", unique=True)
    data = JSONField(default={})
    tags = ArrayField(TextField, default=["", ""])
    loaded = BooleanField(default=False)
    avilable = BooleanField(default=True)
    avilable_updated = BooleanField(default=False)
    is_translated = BooleanField(default=False)
    is_failed = BooleanField(default=False)


class PlIkeaItems(BaseModel):
    url = TextField()
    code = TextField(default="", unique=True)
    data = JSONField(default={})
    tags = ArrayField(TextField, default=["", ""])
    loaded = BooleanField(default=False)
    avilable_updated = BooleanField(default=False)
    avilable = BooleanField(default=True)
    is_translated = BooleanField(default=False)
    is_failed = BooleanField(default=False)


class TgUsers(BaseModel):
    tel_id = BigIntegerField(unique=True)
    mst = TextField(default="")


class Posts(BaseModel):
    item_id = BigIntegerField(unique=True)
    info = JSONField(default={})
    history = ArrayField(TextField, default=list)

