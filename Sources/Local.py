#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pathlib import Path

import Modules.Log as Log

class Local:

    def __init__(self, rootdir):
        self._rootdir = rootdir
        Path(self._rootdir).mkdir(parents=True, exist_ok=True)

    def GetInfo(self):
        Log.Write(f"Local media dorectory is {self._rootdir}")

