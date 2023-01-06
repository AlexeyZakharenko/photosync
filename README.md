# photosync
Простая утлита для переноса фото и видео между Google Photo и локальным хранилищем.

Основная фича - умеет сохранять структуру альбомов. Не удаляет из приемника данные, удаленные в источнике, и это тоже фича.

## Доступные источники

### Google

Для работы необходимы библиотеки клиента Google API (https://github.com/googleapis/google-api-python-client) и Google Cloud проект с включенным Photos Library API (https://developers.google.com/workspace/guides/create-project).

По умолчанию ищет JSON-файл клиента Google в _private/google-client_secret.json_.

Забирает все медиафайлы, включая созданные гуглом коллажи и анимации, в максимально доступном качестве. Геолокации Google не отдает, поэтому без них.

**ВНИМАНИЕ!** У Photos Library API есть квота в 10 000 запросов в день, которая обнуляется в 11:00 по Москве. Первоначальная синхронизация большого архива может растянуться на несколько дней. Рекомендую выполнить в первый день команду `get`, а затем вызывать `put` до тех пор, пока все данные не перенесутся. В дальнейшем можно будет делать `sync` с указанием временного интервала.

### Native
Локальное хранилище пользователя. То, что лежит обычно в папке _Неразобранное_. Может быть только источником.

Все подпапки считаются альбомами, файлы с одинаковыми именами и одинаковым размером считаются одним файлом. Синхронизация из **native** в **local** поможет почистить диск от двойников. 

### Local
Локальное хранилище, созданное утилитой. Руками туда лучше не лазить.

В корневой папке создаются две подпапки _photos_ и _albums_. В первой хранятся все фото с разбивкой по месяцам, чтобы различные DLNA-устройства не тупили на большом количестве файлов в папке. Во второй содержатся папки альбомов, в которые линкуются файлы из папки _photos_.

## Начало работы

0) Убедиться, что установлены python >= 3.8 и pip 
1) Скачать проект
2) Поставить библиотеки Google API: `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`
3) Настроить проект c Photos Library API, создать для него OAuth 2.0 Client Сredentials (scope: https://www.googleapis.com/auth/photoslibrary) и сохранить его json в подпапку _/private_ проекта: _private/google-client_secret.json_
4) Выполнить `photosync.py reset`
5) Изучить `photosync.py -h`
6) Попробовать запустить `photosync.py sync`, при необходимости указав параметры

## Команды

### `reset`
Первое, что надо выполнить после установки. Удаляет всю информацию о пердыдущих синхронизациях и пересоздает окружение для работы. После этой операции следует очистить все, что было в приемнике во избежание дублирования.

### `get`
Получает информацию из источника, обновляет данные для синхронизации. Для получения актуальных данных используйте параметры `--start` и `--end` или `--fromdays`

### `put` 
Ищет несинхронизированные данные и перемещает их из источника в приемник.

### `sync`
Сначала `get`, потом `put`.

### `clean`
Очищает информацию о синхронизированных элементах. Это позволяет повторить операцию `put`, если что-то пошло не так, без повторной загрузки данных из источника. Также следует очистить приемник во избежание дублирования.

### `status`
Выдает информацию об общем и синхронизированном количестве записей в таблицах.
