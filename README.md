# photosync
Простая утилита для регулярного переноса фото и видео между различными облачными и локальными хранилищами.

Основная фича - умеет сохранять структуру альбомов. Не удаляет из приемника данные, удаленные в источнике, и это тоже фича.

## Доступные хранилища

### Google

Для работы необходимы библиотеки клиента Google API (https://github.com/googleapis/google-api-python-client) и Google Cloud проект с включенным Photos Library API (https://developers.google.com/workspace/guides/create-project). Да, проект надо опубликовать, иначе токен авторизации не будет перевыпускаться. Cоздать для него OAuth 2.0 Client Сredentials (scope: https://www.googleapis.com/auth/photoslibrary) и сохранить его конфигурацию в JSON-файл в подпапку _/private_ как _private/google-client_secret.json_.

Забирает все медиафайлы, включая созданные гуглом коллажи и анимации, в максимально доступном через API качестве. Оригинальные файлы этот API отдавть не умеет, так что имейте ввиду. Геолокации Google также не отдает, поэтому без них.

**ВНИМАНИЕ!** У Photos Library API есть квота в 10 000 запросов в день, которая обнуляется в 11:00 по Москве. Первоначальная синхронизация большого архива может растянуться на несколько дней. Рекомендую выполнить в первый день команду `get`, а затем вызывать `put` до тех пор, пока все данные не перенесутся. В дальнейшем можно будет делать `sync` с указанием временного интервала.

### YaDisk

Для работы необходима библиотеки https://github.com/ivknv/yadisk. Также понадобится получить токен для доступа к Яндекс.Диску в соответствии с этой инструкцией: https://yandex.ru/dev/disk/rest/. Токен надо сохранить в TXT-файл в подпапку _/private_ как _private/yandex_token.txt_. Токен выпускается на год, так что надо будет поставить напоминалку на его перевыпуск.

К сожалению, текущая реализация API от Яндекса не позволяет работать с альбомами и создавать линки на файлы. Поэтому, когда **yadisk** является получателем, все фото загружаются в указанный в ключе `--dstroot` корень, а альбомы создаются как папки, в которых создаются копии файлов. Если **yadisk** выступает в качестве источника, сканирование файлов для синхронизации также ведется по файловой системе, начиная с `--srcroot`.

Как только появится вменяемая работа с альбомами, реализую отдельное хранилище **Yandex**, на которое можно будет переключиться, используя базу этого.

### Native
Локальное хранилище пользователя. То, что лежит обычно в папке _Неразобранное_. Может быть только источником.

Все подпапки считаются альбомами, файлы с одинаковыми именами и одинаковым размером считаются одним файлом. Синхронизация из **native** в **local** поможет почистить диск от двойников. 

### Local
Локальное хранилище, созданное утилитой. Руками туда лучше не лазить, но подключить как шарку **Фото** и смотреть на любом DLNA-устройстве - самое то.

В корневой папке создаются две подпапки _photos_ и _albums_. В первой хранятся все фото с разбивкой по месяцам, чтобы различные DLNA-устройства не тупили на большом количестве файлов в папке. Во второй содержатся папки альбомов, в которые линкуются файлы из папки _photos_.

## Начало работы

0) Убедиться, что установлены python >= 3.8 и pip 
1) Скачать проект
2) Поставить необходимые библиотеки:<br>
  `pip install exif`<br>
  `pip install yadisk`<br>
  `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
3) При необходимости настроить проекты в Google и Яндекс, авторизоваться, сохранить токены/конфиги в папке _/private_ (см. описание хранилищ).
4) Изучить `photosync.py -h`
5) Попробовать запустить `photosync.py sync`, при необходимости указав параметры

## Команды

### `get`
Получает информацию из источника, обновляет данные для синхронизации. Для получения актуальных данных используйте параметры `--start` и `--end` или `--fromdays`

### `put` 
Ищет несинхронизированные данные и перемещает их из источника в приемник.

### `sync`
Сначала `get`, потом `put`.

### `clean`
Очищает информацию о синхронизированных элементах. Это позволяет повторить операцию `put`, если что-то пошло не так, без повторной загрузки данных из источника. Также следует очистить приемник во избежание дублирования.
Если указан ключ `--excludealbums`, вместо очистки флагов синхронизации удаляет из таблиц альбомов и связей записи об исключенных альбомах.

### `reset`
Удаляет всю информацию об элементах. После этой операции следует очистить все, что было в приемнике во избежание дублирования.

### `status`
Выдает информацию об общем и синхронизированном количестве записей в таблицах.

## Ключи

### `--help`, `-h` 
Справка. Изучите перед началом работы

### `--src [storage]`, `--dst [storage]` 
Позволяют указать типы хранилищ приемника и получателя.

### `--srcpvt [path]`, `--dstpvt [path]` 
Пути к личным файлам хранилищ источника и приемника. Актуально для **google** и **yadisk**. Если в качестве источника и приемника используются хранилища одного типа (например, переносите фото из одного аккаунта Google в другой), надо указать разные пути. 

### `--srcroot [path]`, `--dstroot [path]` 
Корневые папки хранилищ источника и приемника. Актуально для **yadisk**, **local** и **native**. 

### `--cache [path]`
Папка, которая будет использоваться как временное хранилище переносимых файлов.

### `--dbfile [path/sqlite.db]`
Имя файла БД с таблицами синхронизации. У каждой синхронизации должен быть свой файл.

### `--scope [scope]`
Позволяет указать тип синхронизируемых элементов: `items`, `albums` или `all` (по умолчанию).

### `--strat [YYYY-MM-DD]`
Будут синхронизироваться элементы, созданные в эту дату и позже.

### `--end [YYYY-MM-DD]`
Будут синхронизироваться элементы, созданные в эту дату и раньше.

### `--fromdays [N]`
Будут синхронизироваться элементы за последние `N` дней. Если также указан ключ `--strat', то он  игнорируется.

### `--excludealbums [list | path/list.txt]`
Можно указать названия альбомов, информация о которых не будет сохраняться в таблицы альбомов и связей. Названия можно указать в параметре через запятую либо в файле: кодировка utf-8, каждое название с новой строки (тогда надо передать имя файла).

## Как это использую я
У меня есть отдельный аккаунт Google, куда я сгружаю фото, которые хочу сохранить на память. Т.к. подписка в России сейчас недоступна, места там немного, поэтому я регулярно его чищу.

Так же регулярно на домашнем сервере запускается скрипт, синхронизирующий данные из этого аккаунта в локальное хранилище и на Яндекс.Диск:

## Как это использую я
У меня есть отдельный аккаунт Google, куда я сгружаю фото, которые хочу сохранить на память. Т.к. подписка в России сейчас недоступна, места там немного, поэтому я регулярно его чищу.

Каждую ночь на домашнем сервере запускается скрипт, синхронизирующий данные из этого аккаунта в локальное хранилище и на Яндекс.Диск:

`python -src google -dst local --dstroot /share/photos/google --dbfile db/local.db --fromdays 7`

`python -src google -dst yandex --dstroot /google --dbfile db/yandex.db --fromdays 7`
