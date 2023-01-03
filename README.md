# photosync
Простая утлита для вытягивания фото и видео из Google Photo.

Основная фича - умеет сохранять структуру альбомов.

Для работы необходимы клиент Google API (https://github.com/googleapis/google-api-python-client) и Google Cloud проект с включенным Photos Library API (https://developers.google.com/workspace/guides/create-project)

Как начать работу:

1) Скачать проект
2) Поставить библиотеки Google API: **pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib**
3) Настроить проект c Photos Library API, создать для него OAuth 2.0 Client Сredentials (scope: https://www.googleapis.com/auth/photoslibrary)
   и сохранить его json в подпапку _ _/private_ _ проекта: _ _private/google-client_secret.json_ _
4) Выполнить **photosync.py reset**
5) Изучить **photosync.py -h**
6) Попробовать запустить **photosync.py sync**, при необходимости указав параметры

