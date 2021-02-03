import requests
import logging
from urllib.parse import quote

from app.config import FORMAT, TG_FORMAT, ALARMER_BOT_KEY


class TelegramLogsHandler(logging.Handler):

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def send_message(self, text):
        template = 'https://alarmerbot.ru/?key={key}&message={message}'
        url = template.format(key=self.api_key, message=quote(text))
        try:
            requests.get(url)
        except requests.exceptions.ConnectionError:
            pass

    def emit(self, record):
        log_entry = self.format(record)
        self.send_message(text=log_entry)


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)


# Add alarmer telegram bot handler
tg_handler = TelegramLogsHandler(ALARMER_BOT_KEY)
tg_handler.setLevel(logging.ERROR)
tg_handler.setFormatter(logging.Formatter(TG_FORMAT))
logger.addHandler(tg_handler)

if __name__ == '__main__':
    logger.error('TEST ERROR')