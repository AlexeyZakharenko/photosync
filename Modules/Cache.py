#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
from os import listdir, path, remove
import Modules.Log as Log

class Cache:

    def __init__(self, cachedir):
        self._cachedir = cachedir
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)


    def Clear(self):
        remove(self._cachedir)
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        Log.Write(f"Cache '{self._cachedir}' cleared")
        
    def GetInfo(self):
        Log.Write(f"Cache dir '{self._cachedir}' contains {len([name for name in listdir(self._cachedir) if path.isfile(name)])} files")

