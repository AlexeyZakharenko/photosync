#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import argparse

import SQLite
import Cache

import Google
import Local


def Invoke():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('command', nargs='?', default=Help)
    parser.add_argument('--dbfile', default=Default.DBFile)
    parser.add_argument('--cache', default=Default.CacheDir)
    parser.add_argument('--src', default=Default.Src)
    parser.add_argument('--dst', default=Default.Dst)
    parser.add_argument('--srcprivatedir', default=Default.PrivateDir)
    parser.add_argument('--dstprivatedir', default=Default.PrivateDir)
    parser.add_argument('--srcrootdir', default=Default.RootDir)
    parser.add_argument('--dstrootdir', default=Default.RootDir)

    parameters = parser.parse_args (sys.argv[1:])
    

    Invokable.get(parameters.command, InvokeHelp)(parameters)


def InvokeHelp(parameters):
    print(f"""
Usage: photosync.py [command] [options]

Commands:

help                Show this help (default)
info                Show information about source and destignation
get                 Get info from source
put                 Put data to destignation
sync                Sync source and destignation (get + put)
reset               Clean cache and database

Options:

--src               Type of source. Can be 'google', 'yandex' or 'local'. By default '{Default.Src}'
--dst               Type of source. Can be 'google', 'yandex' or 'local'. By default '{Default.Local}'
--srcprivatedir     Directory for private files (session tokens). Available for 'google' and 'yandex'. By default '{Default.PrivateDir}'
--dstprivatedir     Directory for private files (session tokens). Available for 'google' and 'yandex'. By default '{Default.PrivateDir}'
--srcrootdir            Root directory for media items. Available for 'local'. By default '{Default.RootDir}'
--dstrootdir            Root directory for media items. Available for 'local'. By default '{Default.RootDir}'
--dbfile            SQLite database file. By default '{Default.DBFile}'
--cache             Cache directory. By default '{Default.CacheDir}'
""")


# Defined commands 
Help = 'help'
Reset = 'reset'
Info = 'info'
Get = 'get'


def _getSrc(parameters):
    if (parameters.src == 'google'):
        return Google.Google(parameters.srcprivatedir)

    return Local.Local(parameters.srcrootdir)

def _getDst(parameters):
    if (parameters.dst == 'google'):
        return Google.Google(parameters.dstprivatedir)

    return Local.Local(parameters.dstrootdir)

def InvokeReset(parameters):
    db = SQLite.DB(parameters.dbfile)
    db.DeleteDB()
    db.CreateDB()
    cache = Cache.Cache(parameters.cache)
    cache.Clear()


def InvokeInfo(parameters):
    db = SQLite.DB(parameters.dbfile)
    cache = Cache.Cache(parameters.cache)
    src = _getSrc(parameters)
    dst = _getDst(parameters)

    db.GetInfo()
    cache.GetInfo()
    src.GetInfo()
    dst.GetInfo()


def InvokeGet(parameters):

    src = _getSrc(parameters)
    #items = src.GetItemsInfo()

    albums = src.GetAlbumsInfo()
    db = SQLite.DB(parameters.dbfile)
    #db.UpdateItems(items)
    db.UpdateAlbums(albums)
    

Invokable = {
    Help : InvokeHelp,
    Reset: InvokeReset,
    Info: InvokeInfo,
    Get: InvokeGet
    
}


class Default:
    DBFile = 'db/photosync.db'
    CacheDir = 'cache/' 
    PrivateDir = 'private/' 
    Src = "google"
    Dst = "local"
    RootDir = 'photos/'


