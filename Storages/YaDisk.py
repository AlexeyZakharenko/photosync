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

PHOTOS_PATH = 'photos'
ALBUMS_PATH = 'albums'



class YaDisk:

    def __init__(self, privatedir, rootdir):
        self._privatedir = path.normpath(privatedir)
        self._rootdir = rootdir.replace("\\","/")
        self._photosdir = YaDisk.join(self._rootdir, PHOTOS_PATH)
        self._albumsdir = YaDisk.join(self._rootdir, ALBUMS_PATH)
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
        if not self._service.exists(self._photosdir):
            self._service.mkdir(self._photosdir)
            Log.Write(f"Create photos YaDisk dir {self._photosdir}")
        if not self._service.exists(self._albumsdir):
            self._service.mkdir(self._albumsdir)
            Log.Write(f"Create photos YaDisk dir {self._albumsdir}")

    @staticmethod
    def join(*path):
        return "/".join(path)

    def GetType(self):
        return f"YaDisk ({path.join(self._privatedir, TOKEN_FILE)})"

    def GetStatus(self):
        self._connect()
        Log.Write(self.GetType())

    def GetInfo(self, start=None, end=None, scope='all'):

        items = []
        albums = []

        return (items, albums)

    def PutItem(self, item, cache):
        self._connect()
        try:
            dstId = YaDisk.join(self._photosdir,item.Filename)
            self._service.upload(cache.GetFilename(item.SrcId), dstId, headers={
                "media_type": item.Type,
            }, overwrite=True)

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
            dstId = YaDisk.join(self._albumsdir,album.Title)
            if self._service.exists(dstId):
                album.DstId = dstId;
                Log.Write(f"Album '{album.Title}'  already exists({album.DstId})")
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
            self._service.copy(item.DstId, YaDisk.join(album.DstId, item.Filename), overwrite=True)
            Log.Write(f"Put item '{item.Filename}' into album '{album.Title}' ({item.DstId} -> {album.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' into album '{album.Title}' to YaDisk: {err}")
            return False

        return True
