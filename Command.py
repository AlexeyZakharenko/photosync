#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import argparse

import SQLite
import Cache


def Invoke():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('command', nargs='?', default=Help)
    parser.add_argument('--dbfile', default=Default.DBFile)
    parser.add_argument('--cache', default=Default.CacheDir)

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
""")


# Defined commands 
Help = 'help'
Reset = 'reset'
Info = 'info'

def InvokeReset(parameters):
    db = SQLite.DB(parameters.dbfile)
    db.DeleteDB()
    db.CreateDB()
    cache = Cache.Cache(parameters.cache)
    cache.Clear()

def InvokeInfo(parameters):
    db = SQLite.DB(parameters.dbfile)
    db.GetInfo()

def InvokeGet(parameters):
    cache = Cache.Cache(parameters.cache)


Invokable = {
    Help : InvokeHelp,
    Reset: InvokeReset,
    Info: InvokeInfo
}

class Default:
    DBFile = 'photosync.db'
    CacheDir = 'cache/' 

