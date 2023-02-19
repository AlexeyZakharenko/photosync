#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Item():
    def __init__(self, srcId, filename, dstId=None, created=None, type=None, size=None, sha256=None, patchId=None, sync=None):
        self.SrcId = srcId
        self.Filename = filename
        self.DstId = dstId
        self.Created = created
        self.Type=type
        self.Size = size
        self.SHA256 = sha256
        self.PatchId = patchId
        self.Sync = sync
