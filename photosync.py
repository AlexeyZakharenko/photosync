#!/usr/bin/python
# -*- coding: UTF-8 -*-

if __name__ != '__main__':
    print("Please run as main module")

import sys
import argparse

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

try:
    parser = argparse.ArgumentParser()
    
    parser.add_argument('command', nargs='?', default='help')
    parser.add_argument('--dbfile', default=Default.DBFile)
    parser.add_argument('--cache', default=Default.CacheDir)
    parser.add_argument('--src', default=Default.Src)
    parser.add_argument('--dst', default=Default.Dst)
    parser.add_argument('--srcprivatedir', default=Default.PrivateDir)
    parser.add_argument('--dstprivatedir', default=Default.PrivateDir)
    parser.add_argument('--srcrootdir', default=Default.RootDir)
    parser.add_argument('--dstrootdir', default=Default.RootDir)

    parameters = parser.parse_args (sys.argv[1:])
    
    orchestrator = Orchestrator.Orchestrator(
        cache = Cache.Cache(parameters.cache),
        db = SQLite.DB(parameters.dbfile),
        src = Orchestrator.GetSource(parameters.src, parameters.srcprivatedir, parameters.srcrootdir),
        dst = Orchestrator.GetSource(parameters.dst, parameters.dstprivatedir, parameters.dstrootdir)
    )

    if not orchestrator.Invoke(parameters.command):
        print(f"""
Usage: photosync.py [command] [options]

Commands:

help                Show this help (default)
info                Show information about source and destignation
get                 Get info from source (update database info)
put                 Put data to destignation (according to database info)
sync                Sync source and destignation (get + put)
reset               Clean cache and database

Options:

--src               Type of source. Can be 'google', 'yandex' or 'local'. By default '{Default.Src}'
--dst               Type of source. Can be 'google', 'yandex' or 'local'. By default '{Default.Dst}'
--srcprivatedir     Directory for private files (session tokens). Available for 'google' and 'yandex'. By default '{Default.PrivateDir}'
--dstprivatedir     Directory for private files (session tokens). Available for 'google' and 'yandex'. By default '{Default.PrivateDir}'
--srcrootdir        Root directory for media items. Available for 'local'. By default '{Default.RootDir}'
--dstrootdir        Root directory for media items. Available for 'local'. By default '{Default.RootDir}'
--dbfile            SQLite database file. By default '{Default.DBFile}'
--cache             Cache directory. By default '{Default.CacheDir}'
""")

except Exception as err:
    print("Error: {}".format(err))



