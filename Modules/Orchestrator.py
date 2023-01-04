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
        if command == 'clean':
            return self._invokeClean()
        if command == 'get':
            return self._invokeGet()
        if command == 'put':
            return self._invokePut()
        if command == 'sync':
            return self._invokeSync()
        return False

    def __init__(self, db, cache, src, dst, start, end, scope):
        self._db = db
        self._cache = cache
        self._src = src
        self._dst = dst
        self._start = start
        self._end = end
        self._scope = scope

    def __del__(self):
        del self._db
        del self._cache
        del self._src
        del self._dst

    def _invokeReset(self):
        Log.Write("Resetting local environment...")
        self._db.DeleteDB()
        self._db.CreateDB()
        return True;

    def _invokeClean(self):
        Log.Write("Clean sync results...")
        self._db.Clean()
        return True;

    def _invokeInfo(self):
        Log.Write(f"Source: {self._src.GetType()}, destignation: {self._dst.GetType()}")
        self._db.GetInfo()
        return True
   
    def _invokeGet(self):
        start = f" from {self._start}" if self._start != None else ""
        end = f" to {self._end}" if self._end != None else ""
        Log.Write(f"Getting info from source {self._src.GetType()}{start}{end}...")

        items = self._src.GetItemsInfo(self._start, self._end)
        self._db.UpdateItemsInfo(items)

        if self._scope == 'all':
            albums = self._src.GetAlbumsInfo(self._start, self._end)
            self._db.UpdateAlbumsInfo(albums)

        return True

    def _invokeSync(self):
        return self._invokeGet() and self._invokePut()

    def _putItems(self):
        items = self._db.GetItemsForSync()
        if len(items) > 0:
            n = 0 
            for item in items:
                if self._src.GetItem(item, self._cache) and self._dst.PutItem(item,self._cache):
                    self._db.MarkItemSync(item)
                    n += 1

            Log.Write(f"Put {n} of {len(items)} items from source {self._src.GetType()} to {self._dst.GetType()}, {len(items)-n} items skipped")

    def _putLinks(self):

        links = self._db.GetLinksForSync()
        if len(links) > 0:
            n = 0 
            nAlbums = 0
            for link in links:
                item = self._db.GetItem(link.ItemId)
                if item is None:
                    continue
                if item.DstId is None:
                    Log.Write(f"ERROR: item '{link.ItemId}' not putted yet")
                    continue

                album = self._db.GetAlbum(link.AlbumId)
                if album is None:
                    continue
                if album.DstId is None:
                    if self._dst.PutAlbum(album) and self._db.MarkAlbumSync(album):
                        nAlbums += 1
                    else:
                        continue

                if self._dst.PutItemToAlbum(item, album):
                    self._db.MarkLinkSync(link)
                    n += 1


            Log.Write(f"Put {n} of {len(links)} links and {nAlbums} albums from source {self._src.GetType()} to {self._dst.GetType()}, {len(links)-n} links skipped")

    def _invokePut(self):

        Log.Write(f"Putting data from source {self._src.GetType()} to {self._dst.GetType()}...")

        self._putItems()
        if self._scope == 'all':
            self._putLinks()

        return True



