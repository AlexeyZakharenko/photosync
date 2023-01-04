# photosync
Простая утлита для вытягивания фото и видео из Google Photo.

Основная фича - умеет сохранять структуру альбомов.


## Какие источники поддерживает:

### Google Photo
Пока используется только как источник

Для работы необходимы клиент Google API (https://github.com/googleapis/google-api-python-client) и Google Cloud проект с включенным Photos Library API (https://developers.google.com/workspace/guides/create-project).

Забирает все медиафайлы, включая коллажи и анимации, в максимально доступном качестве. Геолокации Google не отдает, поэтому без них.

### Local
Локальное хранилище. Пока используется как получатель.

В корневой папке создаются две подпапки _photos_ и _albums_. В первую загружаются все фото с разбивкой по месяцам, чтобы различные DLNA-устройства не тупили на большом количестве файлов в папке. Во второй создаются папки альбомов, в которые линкуются файлы из папки _photos_.

## Как начать работу:

0) Убедиться, что установлены python >= 3.8 и pip 
1) Скачать проект
2) Поставить библиотеки Google API: **pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib**
3) Настроить проект c Photos Library API, создать для него OAuth 2.0 Client Сredentials (scope: https://www.googleapis.com/auth/photoslibrary)
   и сохранить его json в подпапку _/private_ проекта: _private/google-client_secret.json_
4) Выполнить **photosync.py reset**
5) Изучить **photosync.py -h**
6) Попробовать запустить **photosync.py sync**, при необходимости указав параметры

