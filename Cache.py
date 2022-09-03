#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
import shutil

import Log

class Cache:

    def __init__(self, cachedir):
        self._cachedir = cachedir
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        Log.Write(f"Use cache {self._cachedir}")


    def Clear(self):
        Log.Write(f"Clearing cache '{self._cachedir}'")

        Log.Write(f"Cache '{self._cachedir}' cleared")
        

