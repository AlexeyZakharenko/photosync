#!/usr/bin/python
# -*- coding: UTF-8 -*-


from os import path, listdir
from datetime import datetime

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album

import Storages.Local as Local



class Native:

    def __init__(self, rootdir):
        self._rootdir = path.normpath(rootdir)
        if not path.isdir(self._rootdir):
            raise Exception(f"Native root directiry {self._rootdir} not found")

    def GetType(self):
        return f"Native ({self._rootdir})"

    def GetStatus(self):
        Log.Write(f"Native root directory is {self._rootdir}")

    def _getInfo(self, subDirs, albumTitle, albums, items, start=None, end=None, scope='all', excludeAlbums=None):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(self._rootdir, subDir)
        for entry in listdir(startDir):
            if entry.startswith('.'):
                continue
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                self._getInfo(subDirs + [entry], entry, albums, items, start, end, scope, excludeAlbums)
            else:
                if Local.LocalTools.GetTypeByName(entry) is None:
                    continue
                size = path.getsize(entryPath)
                item = next((i for i in items if i.Filename == entry and i.Size == size), None)
                if item is None:
                    item = Item.Item(path.join(subDir, entry), entry, size=size)
                    items.append(item)

                # Это корень, не альбом
                if albumTitle is None:
                    continue;

                # В исключениях
                if excludeAlbums != None and albumTitle in excludeAlbums:
                    continue;

                # Раньше не добавляли?
                album = next((a for a in albums if a.SrcId == subDir), None)
                if album is None:
                    album = Album.Album(subDir, albumTitle)
                    albums.append(album)
                
                album.Items.append(item.SrcId)

    def GetInfo(self, start=None, end=None, scope='all', excludeAlbums=None):
        items = []
        albums = []
        # Scan all items to avoid duplicate copies
        try:
            Log.Write(f"Getting items and albums info from Native...")
            self._getInfo([], None, albums, items, start, end, scope, excludeAlbums)
            Log.Write(f"Got info for {len(items)} items and {len(albums)} albums")

        except Exception as err:
            Log.Write(f"ERROR Can't get info from Native: {err}")

        return (items, albums)

    def GetItem(self, item, cache):
        entryPath = path.join(self._rootdir, item.SrcId)
        try:
            type = Local.LocalTools.GetTypeByName(item.Filename)
            time = Local.LocalTools.GetDateTime(entryPath, type)
            with open(entryPath, mode='rb') as file:
                content = file.read()
                size = len(content)
                cache.Store(item.SrcId, content)

            item.Created = time
            item.Type = type

            Log.Write(f"Got item '{item.Filename}' {size}b ({item.SrcId})")

        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.SrcId}' from Native: {err}")
            return False

        return True

    