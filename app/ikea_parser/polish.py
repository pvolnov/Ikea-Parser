from app.translator import Translator
from ukraine import get_translate_ikea_club
from app.logging_config import logger


def translate_product(driver, item, tags):
    ni, tags2 = get_translate_ikea_club(item['code'])
    if ni:
        tags = tags2
        item.iter_update(ni)
    else:
        item, tags = Translator.mtranslate(driver, item, tags)
        logger.debug("mtranslate done", item)

    return item