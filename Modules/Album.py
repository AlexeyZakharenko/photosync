#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Album():
    def __init__(self, srcId, title, dstId=None, sync=0):
        self.SrcId = srcId
        self.Title = title
        self.DstId = dstId
        self.Sync = sync
        self.Items = []
