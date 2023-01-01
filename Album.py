#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Album():
    def __init__(self, id, title):
        self._id = id
        self._title = title
        self._items = []