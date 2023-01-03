#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
from shutil import rmtree
from os import listdir, path, unlink

from atexit import register

import Modules.Log as Log


class Cache:

    def __init__(self, cachedir):
        self._cachedir = path.normpath(cachedir)
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        register(self.Clean)

    def Store(self, filename, content):
        open(path.join(self._cachedir, filename), 'wb').write(content)

    def Get(self, filename):
        fullname = path.join(self._cachedir, filename)
        if path.isfile(fullname):
            return open(fullname, 'rb').read()

        raise Exception(f"File '{filename}' not in cache")

    def Remove(self, filename):
        fullname = path.join(self._cachedir, filename)
        if path.isfile(fullname):
            unlink(fullname)

    def Clean(self):

        for filename in listdir(self._cachedir):
            file_path = path.join(self._cachedir, filename)
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)

        Path(self._cachedir).mkdir(parents=True, exist_ok=True)
        Log.Write(f"Cache '{self._cachedir}' cleaned")
        
    def GetInfo(self):
        Log.Write(f"Cache dir '{self._cachedir}' contains {len([name for name in listdir(self._cachedir) if path.isfile(name)])} files")

