#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path
from shutil import rmtree
from os import listdir, path, unlink
from base64 import urlsafe_b64encode

import Modules.Log as Log


class Cache:

    def __init__(self, cachedir):
        self._cachedir = path.normpath(cachedir)
        Path(self._cachedir).mkdir(parents=True, exist_ok=True)


    def _normaliseName(filename):
        return urlsafe_b64encode(bytes(filename, 'utf-8')).decode('utf-8')
        
    def Store(self, filename, content):
        fullname = path.join(self._cachedir, Cache._normaliseName(filename))
        with open(fullname, mode='wb') as file:
            file.write(content)

    def Get(self, filename):
        fullname = path.join(self._cachedir, Cache._normaliseName(filename))
        if path.isfile(fullname):
            with open(fullname, mode='rb') as file:
                return file.read()

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
        
    def GetStatus(self):
        Log.Write(f"Cache dir '{self._cachedir}' contains {len([name for name in listdir(self._cachedir) if path.isfile(name)])} files")

