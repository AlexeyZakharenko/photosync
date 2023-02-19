#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Required https://pypi.org/project/exif/
# pip install exif


# Interface for sources
#
# -- common methodes
# def GetType(self) -> string
# def GetStatus(self) -> void
#
# -- methodes for source
# def GetInfo(self, start=None, end=None, scope='all') -> (Item[] ->(SrcId,Filename), Album[] -> (SrcId, Title))
# def GetItem(self, item, cache) -> bool, set item.Created->datetime(UTC), item.Type->['image', 'video']
#
# -- methodes for destination
# def PutItem(self, item, cache) -> bool, set item.DstId, 
# def PutAlbum(self, album) -> bool, set album.DstId
# def PutItemToAlbum(self, item, album) -> bool

from pathlib import Path
from os import path, utime, mkdir, link, listdir
from datetime import datetime
from exif import Image

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album

PHOTOS_PATH = 'photos'
ALBUMS_PATH = 'albums'

class Local:

    def __init__(self, rootdir):
        self._rootdir = path.normpath(rootdir)
        self._photosdir = path.join(self._rootdir,PHOTOS_PATH)
        self._albumssdir = path.join(self._rootdir, ALBUMS_PATH)

        Path(self._rootdir).mkdir(parents=True, exist_ok=True)
        Path(self._photosdir).mkdir(parents=True, exist_ok=True)
        Path(self._albumssdir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _getSeconds(dt):
        return int((dt-datetime(1970,1,1)).total_seconds())

    @staticmethod
    def _getItems(root, subDirs, items, start, end):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(root, subDir)
        for entry in listdir(startDir):
            if entry.startswith('.'):
                continue
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                Local._getItems(root, subDirs + [entry], items, start, end)
            else:
                if LocalTools.GetTypeByName(entry) is None:
                    continue
                if start != None or end != None:
                    time = path.getmtime(entryPath)
                    if start != None and start > time:
                        continue;
                    if end != None and end < time:
                        continue;
                items.append(Item.Item(path.join(subDir, entry), entry))

    @staticmethod
    def _getAlbums(root, subDirs, albumTitle, albums, items, excludeAlbums):
        subDir = ''
        for s in subDirs:
            subDir = path.join(subDir, s)
        startDir = path.join(root, subDir)
        for entry in listdir(startDir):
            if entry.startswith('.'):
                continue
            entryPath = path.join(startDir, entry)
            if path.isdir(entryPath):
                Local._getAlbums(root, subDirs + [entry], entry, albums, items, excludeAlbums)
            else:
                # Это корень, не альбом
                if albumTitle is None:
                    continue
                # Ищем документ
                item = next((i for i in items if i.Filename == entry), None)
                # Не в этот раз
                if item is None:
                    continue

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
        try:
            startSec = None if start is None else Local._getSeconds(start)
            endSec = None if end is None else Local._getSeconds(end)

            if scope == 'all' or scope == 'items':
                Log.Write(f"Getting items info from Local...")
                Local._getItems(self._photosdir, [], items, startSec, endSec)
                Log.Write(f"Got info for {len(items)} items")
            if scope == 'all' or scope == 'albums':
                Log.Write(f"Getting albums info from Local...")
                Local._getAlbums(self._albumssdir, [], None, albums, items, excludeAlbums)
                Log.Write(f"Got info for {len(albums)} albums")

        except Exception as err:
            Log.Write(f"ERROR Can't get info from Local: {err}")

        return (items, albums)

    def CheckItem(self, item, type='dst'):
        id = item.DstId if type == 'dst' else item.SrcId; 
        itemPath = path.join(self._photosdir, id)

        if not path.exists(itemPath):
            Log.Write(f"Missed item '{item.Filename}' ({id} {item.SrcId} {item.DstId})")
            return False

        return True


    def GetItem(self, item, cache):
        entryPath = path.join(self._photosdir, item.SrcId)
        try:
            type = LocalTools.GetTypeByName(item.Filename)
            time = LocalTools.GetDateTime(entryPath, type)
            with open(entryPath, mode='rb') as file:
                content = file.read()
                size = len(content)
                cache.Store(item.SrcId, content)

            item.Created = time
            item.Type = type

            Log.Write(f"Got item '{item.Filename}' {size}b ({item.SrcId})")


        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.SrcId}' from Local: {err}")
            return False

        return True

    def PutItem(self, item, cache):
        
        #Generate new title
        try:

            created = Local._getSeconds(item.Created)
            
            dstPath = path.join(item.Created.strftime("%Y"),item.Created.strftime("%m"))
            itemPath = path.join(self._photosdir,dstPath)
            if not path.isdir(itemPath):
                Path(itemPath).mkdir(parents=True, exist_ok=True)

            item.DstId = path.join(dstPath,item.Filename);
            itemPath = path.join(self._photosdir,item.DstId)
            open(itemPath, 'wb').write(cache.Get(item.SrcId))
            utime(itemPath, (created, created))
            Log.Write(f"Put item '{item.Filename}' ({itemPath})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Local: {err}")
            return False

        finally:
            cache.Remove(item.SrcId)

        return True

    def PutAlbum(self, album):
        
        try:

            album.DstId = album.Title
            albumPath = path.join(self._albumssdir, album.DstId)
            if not path.isdir(albumPath):
                Path(albumPath).mkdir(parents=True, exist_ok=True)
                
            Log.Write(f"Put album '{album.Title}' ({albumPath})")

        except Exception as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to Local: {err}")
            return False

        return True

    def PutItemToAlbum(self, item, album):

        try:

            itemPath = path.join(self._photosdir,item.DstId)
            albumPath = path.join(self._albumssdir,album.DstId)
            if not path.exists(itemPath):
                nonExists = item.DstId
                item.DstId = None
                raise Exception(f"Item '{nonExists}' not found")
            if not path.exists(albumPath):
                nonExists = album.DstId
                album.DstId = None
                raise Exception(f"Album '{nonExists}' not found")
                
            targetPath = path.join(albumPath,path.split(item.DstId)[-1])

            link(itemPath, targetPath)
            Log.Write(f"Put item '{item.DstId}' into album '{album.DstId}' ({targetPath})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.DstId}' into album '{album.DstId}' to Local: {err}")
            return False

        return True

    def GetType(self):
        return f"Local ({self._rootdir})"

    def GetStatus(self):
        Log.Write(f"Local media directory is {self._rootdir}")


class LocalTools:

    def GetTypeByName(filename):
        ext = path.splitext(filename)[-1].upper()
        if ext in [".MKV", ".AVI", ".3GP", ".3G2", ".MP4", ".ASF", ".DIVX", ".M2T", ".M2TS", ".M4V", ".MMV", ".MOD", ".MOV", ".MPG", ".MTS", ".TOD", ".WMV"]:
            return 'video'
        if ext in [".JPG", ".PNG", ".GIF", ".BMP", ".HEIC", ".ICO", ".TIFF", ".WEBP", ".RAW"]:
            return 'image'
        return None

    def GetDateTime(filePath, type):
        dt = None
        if type == 'image':
            try:
                with open(filePath, 'rb') as image_file:
                    imageInfo = Image(image_file)
                if imageInfo.has_exif:
                    dt = datetime.strptime(imageInfo.datetime, '%Y:%m:%d %H:%M:%S').replace(tzinfo=None) 
            except:
                dt = None

        if dt == None:
           dt = datetime.utcfromtimestamp(path.getmtime(filePath)) 

        return dt
