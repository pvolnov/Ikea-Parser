from app.logging_config import logger


def translate_to_ru(texts_dict: dict):
    import requests

    URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    API_KEY = 'AQVNz7AiSpbBHL8ZbmsJhwMsSFpOxVMZzWr6aWzc'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }

    def translate_texts(texts):
        body = {
            "folder_id": 'b1gpf6j6ejlihe9f4j2m',
            "texts": texts,
            "targetLanguageCode": "ru"
        }
        response = requests.post(URL, json=body, headers=headers)
        return response.json()

    items = list(texts_dict.items())
    texts = [item[1] for item in items]
    result_json = translate_texts(texts)
    translations = result_json['translations']
    return {
        items[i][0]: translations[i]['text']
        for i in range(len(items))
    }


class A:
    def __iter__(self):
        pass

    def __next__(self):
        pass
if __name__ == '__main__':
    import colorama
    from colorama import Fore, Style

    print(Fore.BLUE + "Hello World")

