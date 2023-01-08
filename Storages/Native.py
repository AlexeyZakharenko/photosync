#!/usr/bin/python
# -*- coding: UTF-8 -*-

from os import path, listdir
from datetime import datetime

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album

class Native:


    def __init__(self, rootdir):
        self._rootdir = path.normpath(rootdir)
        if not path.isdir(self._rootdir):
            raise Exception(f"Native root directiry {self._rootdir} not found")

    def GetType(self):
        return f"Native ({self._rootdir})"

    def GetStatus(self):
        Log.Write(f"Native root directory is {self._rootdir}")

    @staticmethod
    def _getInfo(root, subDirs, albumTitle, albums, items):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(root, subDir)
        for entry in listdir(startDir):
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                Native._getInfo(root, subDirs + [entry], entry, albums, items)
            else:
                size = path.getsize(entryPath)
                item = next((i for i in items if i.Filename == entry and i.Size == size), None)
                if item is None:
                    item = Item.Item(path.join(subDir, entry), entry, size=size)
                    items.append(item)

                # Это корень, не альбом
                if albumTitle is None:
                    continue;

                # Раньше не добавляли?
                album = next((a for a in albums if a.SrcId == subDir), None)
                if album is None:
                    album = Album.Album(subDir, albumTitle)
                    albums.append(album)
                
                album.Items.append(item.SrcId)

    def GetInfo(self, start=None, end=None, scope='all'):
        items = []
        albums = []
        # Scan all items to avoid duplicate copies
        try:
            Log.Write(f"Getting items and albums info from Native...")
            Native._getInfo(path.join(self._rootdir), [], None, albums, items)
            Log.Write(f"Got info for {len(items)} items and {len(albums)} albums")

        except Exception as err:
            Log.Write(f"ERROR Can't get info from Native: {err}")

        return (items, albums)


    def GetItem(self, item, cache):
        entryPath = path.join(self._rootdir, item.SrcId)
        try:
            time = datetime.utcfromtimestamp(path.getmtime(entryPath))

            with open(entryPath, mode='rb') as file:
                content = file.read()
                size = len(content)
                cache.Store(item.SrcId, content)

            item.Created = time
            Log.Write(f"Got item '{item.Filename}' {size}b ({item.SrcId})")

        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.SrcId}' from Native: {err}")
            return False

        return True

    