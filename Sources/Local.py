#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
from os import path, utime, mkdir, link
from datetime import datetime

import Modules.Log as Log

PHOTOS_PATH = 'photos'
ALBUMS_PATH = 'albums'

class Local:

    def GetType(self):
        return f"Local ({self._rootdir})"

    def __init__(self, rootdir):
        self._rootdir = path.normpath(rootdir)
        Path(self._rootdir).mkdir(parents=True, exist_ok=True)
        Path(path.join(self._rootdir,PHOTOS_PATH)).mkdir(parents=True, exist_ok=True)
        Path(path.join(self._rootdir,ALBUMS_PATH)).mkdir(parents=True, exist_ok=True)


    def _getSeconds(dt):
        
        return (dt-datetime(1970,1,1)).total_seconds()

    def PutItem(self, item, cache):
        
        #Generate new title
        try:
            dstId = path.join(self._rootdir,PHOTOS_PATH,item.Filename);
            (name, ext) = path.splitext(dstId)
            n=0
            while path.isfile(dstId):
                n += 1
                dstId=f"{name}_{n}{ext}"

            item.DstId = dstId

            open(item.DstId, 'wb').write(cache.Get(item.SrcId))
            utime(item.DstId, (Local._getSeconds(item.Created), Local._getSeconds(item.Created)))
            Log.Write(f"Put item '{item.Filename}' ({item.DstId})")

            cache.Remove(item.SrcId)

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Local service: {err}")
            return False

        return True

    def PutAlbum(self, album):
        
        #Generate new title
        try:
            dstId = path.join(self._rootdir,ALBUMS_PATH,album.Title)
            name = dstId
            n = 0
            while path.isdir(dstId):
                n += 1
                dstId=f"{name}_{n}"

            album.DstId = dstId
            mkdir(album.DstId)
            Log.Write(f"Put album '{album.Title}' ({album.DstId})")

        except Exception as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to Local service: {err}")
            return False

        return True

    def PutItemToAlbum(self, item, album):

        try:
            targetPath = path.join(album.DstId,path.split(item.DstId)[-1])
            link(item.DstId, targetPath)
            Log.Write(f"Put item '{item.DstId}' into album '{album.DstId}' ({targetPath})")

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.DstId}' into album '{album.DstId}' to Local service: {err}")
            return False

        return True

        

        return False

    def GetInfo(self):
        Log.Write(f"Local media directory is {self._rootdir}")

