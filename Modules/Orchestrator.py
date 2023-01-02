#!/usr/bin/python
# -*- coding: UTF-8 -*-

import Sources.Google as Google
import Sources.Local as Local
import Modules.Log as Log

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

    def __init__(self, db, cache, src, dst, start, end):
        self._db = db
        self._cache = cache
        self._src = src
        self._dst = dst
        self._start = start
        self._end = end

    def __del__(self):
        del self._db
        del self._cache
        del self._src
        del self._dst

    def _invokeReset(self):
        Log.Write("Resetting local environment...")
        self._db.DeleteDB()
        self._db.CreateDB()
        self._cache.Clear()
        return True;

    def _invokeInfo(self):
        Log.Write(f"Source: {self._src.GetType()}, destignation: {self._dst.GetType()}")
        self._cache.GetInfo()
        self._db.GetInfo()
        return True
   
    def _invokeGet(self):
        start = f" from {self._start}" if self._start != None else ""
        end = f" to {self._end}" if self._end != None else ""
        Log.Write(f"Getting info from source {self._src.GetType()}{start}{end}...")

        items = self._src.GetItemsInfo(self._start, self._end)
        self._db.UpdateItems(items)

        albums = self._src.GetAlbumsInfo(self._start, self._end)
        self._db.UpdateAlbums(albums)
        return True

    def _invokePut(self):
        Log.Write(f"Putting data from source {self._src.GetType()} to {self._dst.GetType()}to ...")
        
        return True




