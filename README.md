run in heroku
git push heroku heroku:master

# Ikea parser
*Проект на фрилансе*

Заказчик (телеграм): Michail +380 93 502 08 86

## Описание
[Описание от заказчика (гуглдок)](https://docs.google.com/document/d/1BP4p_9lK6anfS3n6ZSixIh53-0EUCgV5OyBEKHl9AIg/edit)
1. Парсинг всех товаров во всех категориях украниской и польской икеи.
Сайт 

Скрипт на python который проходит по всем разделам сайта ikea.pl, выкачивает и переводит новые товары и обновляет информацию о наличии на старые.


Структура проекта
 - migrations корневая папка миграция alembic
 - app все файлы для парсинга и функцианирования бота
 - в корне лежат конфигурационные файлы

Запуск
```
pipenv shell
pipenv install
python main.py
```

Загрузка на heroku. Бот и обновление базы данных
```
./heroku_upload
```