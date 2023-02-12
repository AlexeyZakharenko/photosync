#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Required https://github.com/ivknv/yadisk
# pip install yadisk

# How to register application with Yandex Disk REST API support see https://yandex.ru/dev/disk/rest/
# Save token string as a yandex_token.txt to the private directory (private/ by default)

from pathlib import Path
from os import path

from atexit import register

try: 
    import yadisk
except ImportError as err:
    raise Exception("Yandex API modules not intalled. Please run 'pip install yadisk")

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album


TOKEN_FILE = 'yandex_token.txt'

class YaDisk:

    def __init__(self, privatedir, rootdir):
        self._privatedir = path.normpath(privatedir)
        self._rootdir = YaDisk.join("disk:",rootdir.replace("\\","/"))
        self._rootdir = self._rootdir.replace("//","/")
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, TOKEN_FILE)):
            raise Exception(f"Please set up Yandex Disk REST API application accroding this manual: https://yandex.ru/dev/disk/rest/ and save OAuth token to {path.join(self._privatedir, TOKEN_FILE)}")
        register(self.__close)

    def __close(self):
        if hasattr(self,"_service"):
            self._service = None
            Log.Write(f"Disconnect from YaDisk")
    
    def _connect(self):
        if hasattr(self,"_service"):
            return
        with open(path.join(self._privatedir, TOKEN_FILE), mode='rt') as file:
            token = file.read()
        self._service = yadisk.YaDisk(token=token)
        if not self._service.check_token():
            raise Exception("Invalid Yandex token. Please renew it.")
        info = self._service.get_disk_info()
        Log.Write(f"Connected to YaDisk Service as {info['user']['login']}")
        if not self._service.exists(self._rootdir):
            self._service.mkdir(self._rootdir)
            Log.Write(f"Create root YaDisk dir {self._rootdir}")

    @staticmethod
    def join(*path):
        return "/".join(path).replace("//","/")

    def GetType(self):
        return f"YaDisk ({path.join(self._privatedir, TOKEN_FILE)})"

    def GetStatus(self):
        self._connect()
        Log.Write(self.GetType())


    def _getInfo(self, subDirs, albumTitle, albums, items, start=None, end=None, scope='all', excludeAlbums=None):

        subDir = YaDisk.join(*subDirs)

        startDir = YaDisk.join(self._rootdir, subDir)
        list = self._service.listdir(startDir, timeout=None)

        dirs = []

        for entry in list:
            if entry['type']  == 'dir':
                dirs.append(entry['name'])
            else:
                # Вообще это надо брать?
                if not entry['media_type'] in ['image', 'video']:
                    continue

                # А был ли раньше?
                item = next((i for i in items if i.SHA256 == entry['sha256']), None)
                if item == None:
                    itemId = YaDisk.join(subDir, entry['name']) if len(subDir) > 0 else entry['name']
                    item = Item.Item(itemId, entry['name'], sha256=entry['sha256'])
                    items.append(item)
                    if len(items) % 100 == 0:
                        Log.Write(f"Scan info for {len(items)} items")
                
                # Это корень, не альбом
                if albumTitle is None:
                    continue

                # В исключениях
                if excludeAlbums != None and albumTitle in excludeAlbums:
                    continue;

                # Теперь альбом
                album = next((a for a in albums if a.SrcId == subDir), None)
                if album is None:
                    album = Album.Album(subDir, albumTitle)
                    albums.append(album)
                album.Items.append(item.SrcId)

        for entry in dirs:
            self._getInfo(subDirs + [entry], entry, albums, items, start, end, scope, excludeAlbums)


    def GetInfo(self, start=None, end=None, scope='all', excludeAlbums=None):
        self._connect()
        items = []
        albums = []
        self._getInfo([], None, albums, items, start=None, end=None, scope='all', excludeAlbums=None)
        return (items, albums)

    def GetItem(self, item, cache):
        self._connect()
        entryPath = YaDisk.join(self._rootdir, item.SrcId)
        try:

            self._service.download(entryPath, cache.GetFilename(item.SrcId), timeout=None)
            info = self._service.get_meta(entryPath)
            item.Type = info['media_type']
            if info.FIELDS.get('exif',None) != None and info['exif'].FIELDS.get('date_time', None) != None:
                date = info['exif']['date_time'].replace(tzinfo=None)
            else:
                date = info['created'].replace(tzinfo=None)

            item.Created = date
            item.Size = info['size']
            Log.Write(f"Got item '{item.Filename}' {item.Size}b ({item.SrcId})")

        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.SrcId}' from Local: {err}")
            cache.Remove(item.SrcId)
            return False

        return True


    def PutItem(self, item, cache):
        self._connect()
        try:
            dstId = YaDisk.join(self._rootdir,item.Filename)
            self._service.upload(cache.GetFilename(item.SrcId), dstId, headers={
                "media_type": item.Type, 
                "created" : item.Created.isoformat()
            }, overwrite=True, timeout=None)

            item.DstId = dstId
            Log.Write(f"Put item '{item.Filename}' ({item.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to YaDisk: {err}")
            return False

        finally:
            cache.Remove(item.SrcId)

        return True

    def PutAlbum(self, album):
        self._connect()
        try:
            dstId = YaDisk.join(self._rootdir,album.Title)
            if self._service.exists(dstId):
                album.DstId = dstId;
                Log.Write(f"Album '{album.Title}' already exists({album.DstId})")
                return True

            self._service.mkdir(dstId)
            album.DstId = dstId

            Log.Write(f"Put album '{album.Title}' ({album.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to YaDisk: {err}")
            return False

        return True

    def PutItemToAlbum(self, item, album):
        self._connect()
        try:
            self._service.copy(item.DstId, YaDisk.join(album.DstId, item.Filename), overwrite=True, timeout=None)
            Log.Write(f"Put item '{item.Filename}' into album '{album.Title}' ({item.DstId} -> {album.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' into album '{album.Title}' to YaDisk: {err}")
            return False

        return True
