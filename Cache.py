#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
from os import listdir, path, remove
import Log

class Cache:

    def __init__(self, cachedir):
        self._cachedir = cachedir
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        Log.Write(f"Use cache {self._cachedir}")


    def Clear(self):
        Log.Write(f"Clearing cache '{self._cachedir}'")
        remove(self._cachedir)
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        Log.Write(f"Cache '{self._cachedir}' cleared")
        
    def GetInfo(self):
        Log.Write(f"Cache dir '{self._cachedir}' contains {len([name for name in listdir(self._cachedir) if path.isfile(name)])} files")

