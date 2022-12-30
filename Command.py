#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import argparse

import SQLite
import Cache
import Google


def Invoke():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('command', nargs='?', default=Help)
    parser.add_argument('--dbfile', default=Default.DBFile)
    parser.add_argument('--cache', default=Default.CacheDir)
    parser.add_argument('--privatedir', default=Default.PrivateDir)

    parameters = parser.parse_args (sys.argv[1:])
    
    Invokable.get(parameters.command, InvokeHelp)(parameters)


def InvokeHelp(parameters):
    print(f"""
Usage: main.py [command] [options]

Commands:

help        Show this help (default)
info        Show information 
get         Get files from source
sync        Sync source and destignation
reset       Clean cache and database

Options:

--dbfile    SQLite database file. By default '{Default.DBFile}'
--cache     Cache directory. By default '{Default.CacheDir}'
--privatedir     Directory for private files (session tokens). By default '{Default.PrivateDir}'
""")


# Defined commands 
Help = 'help'
Reset = 'reset'
Info = 'info'
Get = 'get'


def InvokeReset(parameters):
    db = SQLite.DB(parameters.dbfile)
    db.DeleteDB()
    db.CreateDB()
    cache = Cache.Cache(parameters.cache)
    cache.Clear()
    src = Google.Google(parameters.privatedir)
    src.Clear()

def InvokeInfo(parameters):
    db = SQLite.DB(parameters.dbfile)
    cache = Cache.Cache(parameters.cache)
    src = Google.Google(parameters.privatedir)
    db.GetInfo()
    cache.GetInfo()
    src.GetInfo()

def InvokeGet(parameters):
    cache = Cache.Cache(parameters.cache)
    src = Google.Google(parameters.privatedir)
    

Invokable = {
    Help : InvokeHelp,
    Reset: InvokeReset,
    Info: InvokeInfo,
    Get: InvokeGet
}


class Default:
    DBFile = 'photosync.db'
    CacheDir = 'cache/' 
    PrivateDir = 'private/' 

