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
import Modules.Cache as Cache


TOKEN_FILE = 'yandex_token.txt'


class Yandex:

    def __init__(self, privatedir, rootdir):
        self._privatedir = path.normpath(privatedir)
        self._rootdir = rootdir.replace("\\","/")
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, TOKEN_FILE)):
            raise Exception(f"Please set up Yandex Disk REST API application accroding this manual: https://yandex.ru/dev/disk/rest/ and save OAuth token to {path.join(self._privatedir, TOKEN_FILE)}")
        register(self.__close)

    def __close(self):
        if hasattr(self,"_service"):
            self._service = None
            Log.Write(f"Disconnect from Yandex")
    
    def _connect(self):
        if hasattr(self,"_service"):
            return
        with open(path.join(self._privatedir, TOKEN_FILE), mode='rt') as file:
            token = file.read()
        self._service = yadisk.YaDisk(token=token)
        if not self._service.check_token():
            raise Exception("Invalid Yandex token. Please renew it.")
        if not self._service.exists(self._rootdir):
            self._service.mkdir(self._rootdir)
            Log.Write(f"Create root Yandex dir {self._rootdir}")


    def GetType(self):
        return f"Yandex ({path.join(self._privatedir, TOKEN_FILE)})"

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
            return False    
            dstId = f"{self._rootdir}/{item.Filename}"
            self._service.upload(cache.GetFilename(item.SrcId), dstId, headers={
                "media_type": item.Type,
            })

            item.DstId = dstId
            Log.Write(f"Put item '{item.Filename}' ({item.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Yandex: {err}")
            return False

        finally:
            cache.Remove(item.SrcId)

        return True
