#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Interface for sources
#
# -- common methodes
# def GetType(self) -> string
# def GetStatus(self) -> void
#
# -- methodes for source
# def GetInfo(self, start=None, end=None, scope='all') -> (Item[] ->(SrcId,Filename), Album[] -> (SrcId, Title))
# def GetItem(self, item, cache) -> bool, set item.Created
#
# -- methodes for destination
# def PutItem(self, item, cache) -> bool, set item.DstId, 
# def PutAlbum(self, album) -> bool, set album.DstId
# def PutItemToAlbum(self, item, album) -> bool

from pathlib import Path
from os import path, utime, mkdir, link, listdir
from datetime import datetime

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album

PHOTOS_PATH = 'photos'
ALBUMS_PATH = 'albums'

class Local:

    def __init__(self, rootdir):
        self._rootdir = path.normpath(rootdir)
        Path(self._rootdir).mkdir(parents=True, exist_ok=True)
        Path(path.join(self._rootdir,PHOTOS_PATH)).mkdir(parents=True, exist_ok=True)
        Path(path.join(self._rootdir,ALBUMS_PATH)).mkdir(parents=True, exist_ok=True)

    def _getSeconds(dt):
        return (dt-datetime(1970,1,1)).total_seconds()
    
    def _getItems(root, subDirs, items, start, end):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(root, subDir)
        for entry in listdir(startDir):
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                Local._getItems(root, subDirs + [entry], items, start, end)
            else:
                if start != None or end != None:
                    time = path.getmtime(entryPath)
                    if start != None and start > time:
                        continue;
                    if end != None and end < time:
                        continue;
                items.append(Item.Item(path.join(subDir, entry), entry))

    def _getAlbums(root, subDirs, albumTitle, albums, items):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(root, subDir)
        for entry in listdir(startDir):
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                Local._getAlbums(root, subDirs + [entry], entry, albums, items)
            else:
                # Это корень, не альбом
                if albumTitle is None:
                    continue
                # Ищем документ
                item = next((i for i in items if i.Filename == entry), None)
                # Не в этот раз
                if item is None:
                    continue

                # Раньше не добавляли?
                album = next((a for a in albums if a.SrcId == subDir), None)
                if album is None:
                    album = Album.Album(subDir, albumTitle)
                    albums.append(album)
                
                album.Items.append(item.SrcId)

    def GetInfo(self, start=None, end=None, scope='all'):
        items = []
        albums = []
        try:
            startSec = None if start is None else Local._getSeconds(start)
            endSec = None if end is None else Local._getSeconds(end)

            if scope == 'all' or scope == 'items':
                Log.Write(f"Getting items info from Local...")
                Local._getItems(path.join(self._rootdir,PHOTOS_PATH), [], items, startSec, endSec)
                Log.Write(f"Got info for {len(items)} items")
            if scope == 'all' or scope == 'albums':
                Log.Write(f"Getting albums info from Local...")
                Local._getAlbums(path.join(self._rootdir,ALBUMS_PATH), [], None, albums, items)
                Log.Write(f"Got info for {len(albums)} albums")

        except Exception as err:
            Log.Write(f"ERROR Can't get info from Local: {err}")

        return (items, albums)

    def GetItem(self, item, cache):
        entryPath = path.join(self._rootdir, PHOTOS_PATH, item.SrcId)
        try:
            time = datetime.utcfromtimestamp(path.getmtime(entryPath))
            with open(entryPath, mode='rb') as file:
                content = file.read()
                size = len(content)
                cache.Store(item.SrcId, content)

            item.Created = time
            Log.Write(f"Got item '{item.Filename}' {size}b ({item.SrcId})")


        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.SrcId}' from Local: {err}")
            return False

        return True

    def PutItem(self, item, cache):
        
        #Generate new title
        try:

            created = Local._getSeconds(item.Created)
            
            dstPath = path.join(self._rootdir,PHOTOS_PATH,item.Created.strftime("%Y-%m"))
            if not path.isdir(dstPath):
                Path(dstPath).mkdir(parents=True, exist_ok=True)

            item.DstId = path.join(dstPath,item.Filename);

            open(item.DstId, 'wb').write(cache.Get(item.SrcId))
            utime(item.DstId, (created, created))
            Log.Write(f"Put item '{item.Filename}' ({item.DstId})")

            cache.Remove(item.SrcId)

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Local: {err}")
            return False

        return True

    def PutAlbum(self, album):
        
        try:
            album.DstId = path.join(self._rootdir,ALBUMS_PATH,album.Title)
            mkdir(album.DstId)
            Log.Write(f"Put album '{album.Title}' ({album.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to Local: {err}")
            return False

        return True

    def PutItemToAlbum(self, item, album):

        try:
            targetPath = path.join(album.DstId,path.split(item.DstId)[-1])
            link(item.DstId, targetPath)
            Log.Write(f"Put item '{item.DstId}' into album '{album.DstId}' ({targetPath})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.DstId}' into album '{album.DstId}' to Local: {err}")
            return False

        return True

        

        return False

    def GetType(self):
        return f"Local ({self._rootdir})"

    def GetStatus(self):
        Log.Write(f"Local media directory is {self._rootdir}")

