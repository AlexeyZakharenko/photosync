#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Album():
    def __init__(self, srcId, title, dstId=None):
        self.SrcId = srcId
        self.Title = title
        self.DstId = dstId
        self.Items = []