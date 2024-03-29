#!/usr/bin/python
# -*- coding: UTF-8 -*-

if __name__ != '__main__':
    print("Please run as main module")

import sys
import argparse
from datetime import datetime, timedelta
from os import path

import Modules.SQLite as SQLite
import Modules.Cache as Cache
import Modules.Orchestrator as Orchestrator
import Modules.Log as Log

class Default:
    DBFile = 'db/photosync.db'
    CacheDir = 'cache/' 
    PrivateDir = 'private/' 
    Src = "google"
    Dst = "local"
    RootDir = 'photos/'
    Scope = 'all'

try:

    parser = argparse.ArgumentParser(description='Simple tool for sync photo & video between various sources')
    
    parser.add_argument('command', 
        nargs='?', 
        choices=['status', 'clean', 'put', 'get', 'sync', 'check', 'reset', 'dump'], 
        type=str, 
        help="Available commands.")

    parser.add_argument('--src',
        type=str, 
        choices=['google', 'takeout', 'yadisk', 'local', 'native'], 
        default=Default.Src, 
        help=f"Source. By default '{Default.Src}'.")

    parser.add_argument('--dst', 
        type=str, 
        choices=['google', 'yadisk', 'local'], 
        default=Default.Dst, 
        help=f"Destignation. By default '{Default.Dst}'.")

    parser.add_argument('--scope', 
        type=str, 
        choices=['all','items', 'albums', 'links'], 
        default=Default.Scope, 
        help=f"Scope of sync. By default '{Default.Scope}'.")

    parser.add_argument('--srcpvt', 
        type=str, 
        default=Default.PrivateDir, 
        help=f"Directory for source private files (session tokens etc). By default '{Default.PrivateDir}'.")

    parser.add_argument('--dstpvt', 
        type=str, 
        default=Default.PrivateDir, 
        help=f"Directory for destignation private files (session tokens etc). By default '{Default.PrivateDir}'.")
    
    parser.add_argument('--srcroot', 
        type=str, 
        default=Default.RootDir, 
        help=f"Source root directory. By default '{Default.RootDir}'.")

    parser.add_argument('--dstroot', 
        type=str, 
        default=Default.RootDir, 
        help=f"Destignation root directory. By default '{Default.RootDir}'.")

    parser.add_argument('--dbfile', 
        type=str, 
        default=Default.DBFile, 
        help=f"SQLite database file. By default '{Default.DBFile}'.")

    parser.add_argument('--cache', 
        type=str, 
        default=Default.CacheDir, 
        help=f"Cache directory. By default '{Default.CacheDir}'.")

    parser.add_argument('--start', 
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'), 
        help="Date 'YYYY-MM-DD' from which the data will be synchronized. By default None.")

    parser.add_argument('--end', 
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'), 
        help="Date 'YYYY-MM-DD' up to which the data will be synchronized. By default None.")

    parser.add_argument('--fromdays', 
        type=int, 
        help="For how many last days data will be synchronized. By default None.")

    parser.add_argument('--excludealbums', 
        type=str, 
        help="List of albums to exclude. Can be file like albums.txt (album title per line, utf-8) or list of album titles divided by comma. By default None.")

    parser.add_argument('--fix',
        action="store_true",
        help=f"Fix something depends on command. By default absent.")

    parameters = parser.parse_args (sys.argv[1:])

    def isStr(s):
        return len(s)>0
    albums = None
    if parameters.excludealbums != None:
        if path.isfile(parameters.excludealbums):
            with open(parameters.excludealbums, 'r', encoding='utf-8') as f:
                albums = list(filter(isStr, map(str.strip,f.readlines())))
        else:
            albums = list(filter(isStr, map(str.strip,parameters.excludealbums.split(','))))                    


    orchestrator = Orchestrator.Orchestrator(
        cache = Cache.Cache(parameters.cache),
        db = SQLite.DB(parameters.dbfile),
        src = Orchestrator.GetSource(parameters.src, parameters.srcpvt, parameters.srcroot),
        dst = Orchestrator.GetSource(parameters.dst, parameters.dstpvt, parameters.dstroot),
        start = (datetime.today()-timedelta(days=parameters.fromdays)) if parameters.fromdays != None else parameters.start,
        end = parameters.end,
        scope = parameters.scope,
        excludeAlbums=albums,
        fix = parameters.fix
    )

    if not orchestrator.Invoke(parameters.command):
        parser.print_help()
        
    del orchestrator

except Exception as err:
        Log.Write(f"ERROR {err}")



