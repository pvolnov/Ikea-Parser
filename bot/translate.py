import re
import pickle
import time
import re

from yandex_translate import YandexTranslate, YandexTranslateException


class Translate:
    admins_eljur = ["trnsl.1.1.20200308T225328Z.b767b2a6ef31c40a.8b7eba7acd87791f355c05ef0af3591142f2d438",
                    "trnsl.1.1.20200308T225442Z.c053dfc6c66b5055.cfaa546cb0afc80aad1ed2d1cb74bc5b74f81c2d",
                    "trnsl.1.1.20200308T230307Z.9f16335a639584c0.fb0b572463e504c3ee5af11535eb0e4582573b6e",
                    "trnsl.1.1.20200308T230408Z.7b856b3c7c443fe1.cfdbb0935cce4767c9197c3a4413747e899f0047",
                    "trnsl.1.1.20200308T230444Z.5aac4ff061c85ac8.d970fb7783f9dcfb809c5d1c0477fc0326e3efcf",
                    "trnsl.1.1.20200308T230514Z.f9de525ec42901d1.153f4a283607343e1d200aa53cdaa17230cc07e6",
                    "trnsl.1.1.20200308T230544Z.a57dd53ab58ec396.8f2468d24814af9ff068eb80ffe5f86641e755b5",
                    "trnsl.1.1.20200308T230607Z.35ae236850e17248.43d02cc65c78c0e30f397a124c4d53621b38b852",
                    "trnsl.1.1.20200308T230634Z.1f61e3ab7c1fc36a.28b0c89583af5a02e73ae30b40d32a9b5bff03fc",
                    "trnsl.1.1.20200309T000057Z.76569c2d74d5278f.f082ea6ef0335cc87b76f46fda9716610196a21e",
                    "trnsl.1.1.20200309T000500Z.dc68aef1f414cfb2.8c0597409e3689e0492098e451484d32d8f8c101",
                    "trnsl.1.1.20200309T000542Z.6b68f369a9db2027.5c52366fe1350b579d1c02fc31021559f9b609e3",
                    "trnsl.1.1.20200309T000644Z.82aab5465e7f022c.2c373b1fd81083c1a8e073d22975469a4c4eea14",
                    "trnsl.1.1.20200309T000710Z.c2b63e78c3c18c59.1e65422257eaefb64ed97658ee1d699fdc56234a",
                    "trnsl.1.1.20200309T000736Z.0424d58280ba6aa4.72b146df67d67f8ae7a0754bf9efbaa350f2450a",
                    "trnsl.1.1.20200309T000803Z.37373c2cab31006a.90bbc001d93ba9e075fc26c540ba692c7c8c72dc",
                    "trnsl.1.1.20200309T000830Z.6115b269a8289769.1ecb15beb95d28c42345a5622a448e7aa19145b3",
                    "trnsl.1.1.20200309T000856Z.b4d872ebfb13b510.e5f2c2ee2ef57a91230675ad452691257a50143b",
                    "trnsl.1.1.20200309T000928Z.6de34a43d5ace975.21eae22de7e959e85884b978ca122f73614ce4a9",
                    "trnsl.1.1.20200307T123813Z.70c83c6206c8921b.3ecacd3a28e2816f3420216adaa476672441724c",
                    "trnsl.1.1.20200307T120910Z.a9aa3529aea80de9.f48c7d9b70326a912a7dbdd8f9c32c3e3da2cf96",
                    "trnsl.1.1.20200307T124015Z.7a97880b12c590b9.5a87841600f6a17efa9525acd58d21132cc2b5f0"]
    k = 2

    def __init__(self):
        self.translate = YandexTranslate(self.admins_eljur[self.k])

    def yandex_translate_item(self, item):
        item["discr"] = re.sub("\d+\.\d+\.\d+", "", item["discr"])
        item["details"] = re.sub("\d+\.\d+\.\d+", "", item["details"])

        cats = ["name", "surname", "discr", "dimensions", "instructions", "material", "details", "rules"]
        final_cats = []
        parts = []

        for cat in cats:
            if item[cat] != "" and item[cat] != "\n":
                parts.append(item[cat])
                final_cats.append(cat)
        try:
            res = self.translate.translate(parts, 'pl-ru')
            for i in range(len(final_cats)):
                item[final_cats[i]] = res["text"][i]

            item["tags"] = self.translate.translate(item["tags"], 'pl-ru')["text"]
        except YandexTranslateException:
            self.k = (self.k + 1) % len(self.admins_eljur)
            self.translate = YandexTranslate(self.admins_eljur[self.k])
            # print("change yandex API token")
            # return self.yandex_translate_item(item)
            return item 

        return item