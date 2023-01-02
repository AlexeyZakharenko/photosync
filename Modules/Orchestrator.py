#!/usr/bin/python
# -*- coding: UTF-8 -*-

import Sources.Google as Google
import Sources.Local as Local

def GetSource(type, privateDir, rootDir):
    if type == 'google':
        return Google.Google(privateDir)
    if type == 'local':
        return Local.Local(rootDir)
    raise Exception(f"Unsupported source type '{type}'")


class Orchestrator:


    def Invoke(self, command):
        if command == 'info':
            return self._invokeInfo()
        if command == 'reset':
            return self._invokeReset()
        if command == 'get':
            return self._invokeGet()
        return False

    def __init__(self, db, cache, src, dst):
        self._db = db
        self._cache = cache
        self._src = src
        self._dst = dst

    def _invokeReset(self):
        self._db.DeleteDB()
        self._db.CreateDB()
        self._cache.Clear()
        return True;

    def _invokeInfo(self):
        self._db.GetInfo()
        self._cache.GetInfo()
        self._src.GetInfo()
        self._dst.GetInfo()
        return True
   
    def _invokeGet(self):
        items = self._src.GetItemsInfo()
        albums = self._src.GetAlbumsInfo()
        self._db.UpdateItems(items)
        self._db.UpdateAlbums(albums)
        return True

    def _invokePut(self):
        return True




