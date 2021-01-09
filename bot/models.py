from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField, JSONField

bdname = 'ikea'
bduser = 'postgres'
bdpassword = 'nef441'
bdhost = 'sw.neafiol.site'
bdport = 5432

db = PostgresqlExtDatabase(bdname, user=bduser, password=bdpassword,
                           host=bdhost, port=bdport)  # .rollback()

ALAMER = "df548f-61ac83-624ea4"


class IkeaItems(Model):
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

    class Meta:
        database = db


class Tasks(Model):
    url = TextField(unique=True)
    updted = BooleanField(default=False)
    loaded = BooleanField(default=False)

    class Meta:
        database = db


class UaIkeaItems(Model):
    url = TextField()
    code = TextField(default="", unique=True)
    data = JSONField(default={})
    tags = ArrayField(TextField, default=["", ""])
    loaded = BooleanField(default=False)
    avilable = BooleanField(default=True)
    avilable_updated = BooleanField(default=False)

    class Meta:
        database = db


class PlIkeaItems(Model):
    url = TextField()
    code = TextField(default="", unique=True)
    data = JSONField(default={})
    tags = ArrayField(TextField, default=["", ""])
    loaded = BooleanField(default=False)
    avilable_updated = BooleanField(default=False)
    avilable = BooleanField(default=True)

    class Meta:
        database = db


class TgUsers(Model):
    tel_id = BigIntegerField(unique=True)
    mst = TextField(default="")

    class Meta:
        database = db


class Posts(Model):
    item_id = BigIntegerField(unique=True)
    info = JSONField(default={})
    history = ArrayField(TextField, default=list)

    class Meta:
        database = db


if __name__ == "__main__":
    # with open("../plitems_tags","wb") as f:
    #     pickle.dump([{"code":i.code,"tags":i.tags,"data":i.data} for i in PlIkeaItems.select().execute()],f)

    # PlIkeaItems.drop_table()
    # Posts.create_table()
    # UaIkeaItems.drop_table()
    # UaIkeaItems.create_table()

    print(UaIkeaItems.select().where(UaIkeaItems.avilable_updated == True).count())
    print(UaIkeaItems.select().where((UaIkeaItems.avilable_updated == True) & (
        UaIkeaItems.data["Личные_заметки"].cast("text").contains("Ошибка"))).count())

    # print(UaIkeaItems.get(UaIkeaItems.code=="30373588").avilable)
    # print(UaIkeaItems.get(UaIkeaItems.code=="19185433").avilable)
    # print(UaIkeaItems.get(UaIkeaItems.code=="19185433").avilable_updated)
    # print(UaIkeaItems.get(UaIkeaItems.code=="30373588").avilable_updated)
    # UaIkeaItems.update({UaIkeaItems.avilable:True}).execute()
    # UaIkeaItems.update({UaIkeaItems.avilable:False}).execute()
    # "yc782y09y9y094A"
