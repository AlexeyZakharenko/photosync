#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sqlite3

from os import path
from pathlib import Path

import Log

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
        Log.Write("Creating table 'photos'...")
        cursor = self._connection.cursor()        
        cursor.execute("""CREATE TABLE IF NOT EXISTS photos(
   pictireid INT PRIMARY KEY,
   srcname TEXT,
   dstname TEXT)
    """)
        self._connection.commit()
        Log.Write("Table 'photos' created")

    def DeleteDB(self):
        Log.Write("Deleting table 'photos'...")
        cursor = self._connection.cursor()        
        cursor.execute("DROP TABLE IF EXISTS photos")
        self._connection.commit()
        Log.Write("Table 'photos' deleted")

    def GetInfo(self):
        cursor = self._connection.cursor()        
        cursor.execute("SELECT COUNT(*) AS NRECORDS FROM photos")
        records = cursor.fetchall()
        Log.Write(f"Table 'photos' has {records[0][0]} records")
        return

