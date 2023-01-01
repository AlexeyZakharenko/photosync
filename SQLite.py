#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sqlite3

from os import path
from pathlib import Path

import Log

TABLE_ITEMS = 'items'
TABLE_ALBUMS = 'albums'

class DB(object):

    def __init__(self, dbfile):
        dir = path.split(path.abspath(dbfile))
        Path(dir[0]).mkdir(parents=True, exist_ok=True)
        self._filename = dbfile
        self._connection = sqlite3.connect(self._filename)
        Log.Write(f"Connect to SQLite DB '{self._filename}'")
        
    def __del__(self):
        if hasattr(self,"_connection"):
            self._connection.close()
            Log.Write(f"Disconnect from SQLite DB '{self._filename}'")
    

    def CreateDB(self):
        Log.Write(f"Creating table '{TABLE_ITEMS}'...", end='')
        cursor = self._connection.cursor()        
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ITEMS}(
   srcid TEXT PRIMARY KEY,
   filename TEXT,
   dstid TEXT)
    """)
        self._connection.commit()
        Log.Write("Ok!", date=None)

        Log.Write(f"Creating table '{TABLE_ALBUMS}'...", end='')
        cursor = self._connection.cursor()        
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ALBUMS}(
   albumid TEXT PRIMARY KEY,
   title TEXT,
   itemid TEXT)
    """)
        self._connection.commit()
        Log.Write("Ok!", date=None)

    def DeleteDB(self):
        Log.Write(f"Deleting table '{TABLE_ITEMS}'...", end='')
        cursor = self._connection.cursor()        
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_ITEMS}")
        self._connection.commit()
        Log.Write("Ok!", date=None)
        Log.Write(f"Deleting table '{TABLE_ALBUMS}'...", end='')
        cursor = self._connection.cursor()        
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_ALBUMS}")
        self._connection.commit()
        Log.Write("Ok!", date=None)

    def GetInfo(self):
        cursor = self._connection.cursor()        
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ITEMS}")
        records = cursor.fetchall()
        Log.Write(f"Table '{TABLE_ITEMS}' has {records[0][0]} records")

