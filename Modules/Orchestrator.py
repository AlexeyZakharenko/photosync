#!/usr/bin/python
# -*- coding: UTF-8 -*-

import Storages.Google as Google
import Storages.Takeout as Takeout
import Storages.YaDisk as YaDisk
import Storages.Local as Local
import Storages.Native as Native

import Modules.Log as Log

def GetSource(type, privateDir, rootDir):
    if type == 'google':
        return Google.Google(privateDir)
    if type == 'takeout':
        return Takeout.Takeout(rootDir)
    if type == 'yadisk':
        return YaDisk.YaDisk(privateDir, rootDir)
    if type == 'local':
        return Local.Local(rootDir)
    if type == 'native':
        return Native.Native(rootDir)
    raise Exception(f"Unsupported storage type '{type}'")

class Orchestrator:


    def Invoke(self, command):
        if command == 'status':
            return self._invokeStatus()
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
        if command == 'check':
            return self._invokeCheck()
        if command == 'dump':
            return self._invokeDump()
        return False

    def __init__(self, db, cache, src, dst, start, end, scope, excludeAlbums, fix):
        self._db = db
        self._cache = cache
        self._src = src
        self._dst = dst
        self._start = start
        self._end = end
        self._scope = scope
        self._excludeAlbums = excludeAlbums
        self._fix = fix


    def __del__(self):
        del self._db
        del self._cache
        del self._src
        del self._dst

    def _invokeReset(self):
        if input(f"Are You sure to reset ALL data at '{self._db.GetDBFile()}'? (Yes/No) ") != 'Yes':
            return True
        Log.Write("Resetting local environment...")
        self._db.DeleteDB()
        self._db.CreateDB()
        self._cache.Clean()
        Log.Write("Done! Don't forget to erase destination data.")
        return True

    def _invokeClean(self):
        if input(f"Are You sure to clean {self._scope if self._excludeAlbums == None else 'and remove excluded albums'} data at '{self._db.GetDBFile()}'? (Yes/No) ") != 'Yes':
            return True
        Log.Write("Clean data...")
        self._db.Clean(self._scope, self._excludeAlbums)
        self._cache.Clean()
        return True

    def _invokeStatus(self):
        Log.Write(f"Source: {self._src.GetType()}, destination: {self._dst.GetType()}")
        self._db.GetStatus()
        return True

    def _invokeDump(self):
        self._db.Dump()
        return True

    def _invokeGet(self):
        start = f" from {self._start.date()}" if self._start != None else ""
        end = f" to {self._end.date()}" if self._end != None else ""
        Log.Write(f"Getting info from source {self._src.GetType()}{start}{end}...")

        (items, albums) = self._src.GetInfo(self._start, self._end, self._scope, self._excludeAlbums)

        if self._scope == 'all' or self._scope == 'items':
            self._db.UpdateItemsInfo(items)
        if self._scope == 'all' or self._scope == 'albums':
            self._db.UpdateAlbumsInfo(albums)

        return True

    def _invokeSync(self):
        return self._invokeGet() and self._invokePut()

    def _putItems(self):
        items = self._db.GetItemsForSync()
        Log.Write(f"Putting items from {self._src.GetType()} to {self._dst.GetType()}...")
        if len(items) > 0:
            n = 0 
            for item in items:
                if self._src.GetItem(item, self._cache) and self._dst.PutItem(item,self._cache):
                    self._db.MarkItemSync(item)
                    n += 1

            Log.Write(f"Put {n} of {len(items)} items from {self._src.GetType()} to {self._dst.GetType()}, {len(items)-n} items skipped")

    def _putAlbums(self):
        albums = self._db.GetAlbumsForSync()
        Log.Write(f"Putting albums from {self._src.GetType()} to {self._dst.GetType()}...")
        if len(albums) > 0:
            n = 0 
            for album in albums:
                if album is None:
                    continue
                if album.DstId is None or album.Sync == 0:
                    if self._dst.PutAlbum(album) and self._db.MarkAlbumSync(album):
                        n += 1
                    else:
                        continue

            Log.Write(f"Put {n} of {len(albums)} albums from {self._src.GetType()} to {self._dst.GetType()}, {len(albums)-n} albums skipped")


    def _putLinks(self):
        links = self._db.GetLinksForSync()
        Log.Write(f"Putting links from {self._src.GetType()} to {self._dst.GetType()}...")
        if len(links) > 0:
            n = 0 
            nAlbums = 0
            for link in links:
                item = self._db.GetItem(link.ItemId)
                if item is None:
                    Log.Write(f"WARNING: item '{link.ItemId}' not getted yet. Please get item info from source.")
                    continue
                if item.DstId is None:
                    Log.Write(f"WARNING: item '{link.ItemId}' not putted yet. Please put item to destination.")
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
                else:
                    if item.DstId is None:
                        self._db.MarkItemSync(item, 0)
                    if album.DstId is None:
                        self._db.MarkAlbumSync(album, 0)

            Log.Write(f"Put {n} of {len(links)} links and {nAlbums} albums from {self._src.GetType()} to {self._dst.GetType()}, {len(links)-n} links skipped")


    def _invokePut(self):

        Log.Write(f"Putting data from {self._src.GetType()} to {self._dst.GetType()}...")
        if self._scope == 'all' or self._scope == 'items':
            self._putItems()
        if self._scope == 'all' or self._scope == 'albums':
            self._putAlbums()
        if self._scope == 'all' or self._scope == 'links':
            self._putLinks()

        return True

    def _invokeCheck(self):

        if self._fix and input(f"Are You sure to fix data at '{self._db.GetDBFile()}' (please run first time without '--fix' flag)? (Yes/No) ") != 'Yes':
            return True

        if self._scope == 'all' or self._scope == 'items':
            self._checkItems(self._fix)
        if self._scope == 'all' or self._scope == 'albums':
            self._checkAlbums(self._fix)
        if self._scope == 'all' or self._scope == 'links':
            self._checkLinks(self._fix)

        return True

    def _checkItems(self, fix=False):
        items = self._db.GetItemsForCheck()
        Log.Write(f"Checking items for {self._dst.GetType()}...")
        if len(items) > 0:
            correct = 0 
            missed = 0
            restored = 0
            for item in items:
                exists = self._dst.CheckItem(item)
                if exists and item.Sync != 0:
                    correct += 1
                if not exists and item.Sync == 0:
                    correct += 1
                if exists and item.Sync == 0:
                    restored += 1
                    if fix:
                        self._db.MarkItemSync(item, 1)
                if not exists and item.Sync != 0:
                    missed += 1
                    if fix:
                        self._db.MarkItemSync(item, 0)

            Log.Write(f"Check {len(items)} items from {self._src.GetType()}, {correct} correct, {missed} missed, {restored} unexpected exist")

        return

    def _checkAlbums(self, fix=False):
        albums = self._db.GetAlbumsForCheck()
        Log.Write(f"Checking albums for {self._dst.GetType()}...")
        if len(albums) > 0:
            correct = 0 
            missed = 0
            restored = 0
            for album in albums:
                exists = self._dst.CheckAlbum(album)
                if exists and album.Sync != 0:
                    correct += 1
                if not exists and album.Sync == 0:
                    correct += 1
                if exists and album.Sync == 0:
                    restored += 1
                    if fix:
                        self._db.MarkAlbumSync(album, 1)
                if not exists and album.Sync != 0:
                    missed += 1
                    if fix:
                        self._db.MarkAlbumSync(album, 0)

            Log.Write(f"Check {len(albums)} albums from {self._src.GetType()}, {correct} correct, {missed} missed, {restored} unexpected exist")
        
        return

    def _checkLinks(self, fix=False):
        links = self._db.GetLinksForCheck()
        Log.Write(f"Checking links for {self._dst.GetType()}...")
        if len(links) > 0:
            correct = 0 
            missed = 0
            restored = 0
            for link in links:
                album = self._db.GetAlbum(link.AlbumId)
                item = self._db.GetItem(link.ItemId)

                exists = self._dst.CheckLink(item, album, link)
                if exists and link.Sync != 0:
                    correct += 1
                if not exists and link.Sync == 0:
                    correct += 1
                if exists and link.Sync == 0:
                    restored += 1
                    if fix:
                        self._db.MarkLinkSync(link, 1)
                if not exists and link.Sync != 0:
                    missed += 1
                    if fix:
                        self._db.MarkLinkSync(link, 0)

            Log.Write(f"Check {len(links)} links from {self._src.GetType()}, {correct} correct, {missed} missed, {restored} unexpected exist")
        
        return
