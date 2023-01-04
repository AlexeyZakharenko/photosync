#!/usr/bin/python
# -*- coding: UTF-8 -*-

if __name__ != '__main__':
    print("Please run as main module")

import sys
import argparse
from datetime import datetime, timedelta

import Modules.SQLite as SQLite
import Modules.Cache as Cache
import Modules.Orchestrator as Orchestrator

class Default:
    DBFile = 'db/photosync.db'
    CacheDir = 'cache/' 
    PrivateDir = 'private/' 
    Src = "google"
    Dst = "local"
    RootDir = 'photos/'
    Scope = 'all'

try:

    parser = argparse.ArgumentParser(description='Simple tool for download photo & video from the Google cloud')
    
    parser.add_argument('command', 
            nargs='?', 
            choices=['info', 'clean', 'put', 'get', 'sync'], 
            type=str, 
            help="Available commands: reset (run it at the first time!), info, clean, put, get and sync.")

    parser.add_argument('--src', 
            type=str, 
            choices=['google','local'], 
            default=Default.Src, 
            help=f"Source. Can be 'google', 'yandex' or 'local'. By default '{Default.Src}'.")

    parser.add_argument('--dst', 
            type=str, 
            choices=['google','local'], 
            default=Default.Dst, 
            help=f"Destignation. Can be 'google', 'yandex' or 'local'. By default '{Default.Dst}'.")

    parser.add_argument('--scope', 
            type=str, 
            choices=['all','items'], 
            default=Default.Scope, 
            help=f"Scope of sync. Can be 'all' or 'items'. By default '{Default.Scope}'.")

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
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(), 
            help="Date 'YYYY-MM-DD' from which the data will be synchronized. By default None.")

    parser.add_argument('--end', 
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(), 
            help="Date 'YYYY-MM-DD' up to which the data will be synchronized. By default None.")

    parser.add_argument('--fromdays', 
            type=int, 
            help="For how many last days data will be synchronized. By default None.")

    parameters = parser.parse_args (sys.argv[1:])

    orchestrator = Orchestrator.Orchestrator(
        cache = Cache.Cache(parameters.cache),
        db = SQLite.DB(parameters.dbfile),
        src = Orchestrator.GetSource(parameters.src, parameters.srcpvt, parameters.srcroot),
        dst = Orchestrator.GetSource(parameters.dst, parameters.dstpvt, parameters.dstroot),
        start = (datetime.today()-timedelta(days=parameters.fromdays)).date() if parameters.fromdays != None else parameters.start,
        end = parameters.end,
        scope = parameters.scope
    )

    if not orchestrator.Invoke(parameters.command):
        parser.print_help()
        
    del orchestrator

except Exception as err:
    print("Error: {}".format(err))



