#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sqlite3

from os import path
from pathlib import Path

import Modules.Log as Log

TABLE_ITEMS = 'items'
TABLE_ALBUMS = 'albums'
TABLE_LINKS = 'links'

class DB(object):

    def __init__(self, dbfile):
        dir = path.split(path.abspath(dbfile))
        Path(dir[0]).mkdir(parents=True, exist_ok=True)
        self._filename = dbfile
        
    def _connect(self):
        if not hasattr(self,"_connection"):
            self._connection = sqlite3.connect(self._filename)
            Log.Write(f"Connect to SQLite DB '{self._filename}'")

    def __del__(self):
        if hasattr(self,"_connection"):
            self._connection.close()
            Log.Write(f"Disconnect from SQLite DB '{self._filename}'")

    def CreateDB(self):
        self._connect()
        cursor = self._connection.cursor()        

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ITEMS}(
   srcId TEXT PRIMARY KEY,
   filename TEXT,
   dstId TEXT)
    """)
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ITEMS}' created")

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ALBUMS}(
   albumId TEXT PRIMARY KEY,
   title TEXT)
    """)
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ALBUMS}' created")

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_LINKS}(
   albumId TEXT,
   itemId TEXT,
   FOREIGN KEY(albumId) REFERENCES {TABLE_ALBUMS}(albumId),
   FOREIGN KEY(itemId) REFERENCES {TABLE_ITEMS}(srId))
    """)
        self._connection.commit()
        Log.Write(f"Table '{TABLE_LINKS}' created")

    def DeleteDB(self):
        self._connect()
        cursor = self._connection.cursor()        
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_LINKS}")
        self._connection.commit()
        Log.Write(f"Table '{TABLE_LINKS}' deleted")
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_ITEMS}")
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ITEMS}' deleted")
        cursor = self._connection.cursor()        
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_ALBUMS}")
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ALBUMS}' deleted")

    def GetInfo(self):
        self._connect()
        cursor = self._connection.cursor()        
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ITEMS}")
        itemRecords = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ALBUMS}")
        albumRecords = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_LINKS}")
        linksRecords = cursor.fetchall()
        Log.Write(f"Table records info: '{TABLE_ITEMS}':{itemRecords[0][0]}, '{TABLE_ALBUMS}':{albumRecords[0][0]}, '{TABLE_LINKS}':{linksRecords[0][0]}")

    def UpdateItems(self,items):
        self._connect()
        Log.Write(f"Insert {len(items)} records into '{TABLE_ITEMS}'...")
        try:
            cursor = self._connection.cursor()
            total = 0
            skipped = 0
            inserted = 0

            for item in items:

                cursor.execute(f"SELECT * FROM {TABLE_ITEMS} WHERE srcId == ?", (item._id,))
                found = cursor.fetchone()
                if found is None:
                    cursor.execute(f"INSERT INTO {TABLE_ITEMS} (srcId, filename) VALUES (?, ?)", (item._id, item._filename,))
                    inserted += 1
                else:
                    skipped += 1

                total += 1
                if total % 1000 == 0: 
                    Log.Write(f"{total} records processed")

            self._connection.commit()
            Log.Write(f"{total} records processed, {skipped} skipped, {inserted} inserted into '{TABLE_ITEMS}'")
        
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't insert records: {err}")
        
    def UpdateAlbums(self,albums):
        self._connect()
        Log.Write(f"Insert {len(albums)} records into '{TABLE_ALBUMS}'...")
        try:
            cursor = self._connection.cursor()
            total = 0
            skipped = 0
            inserted = 0
            linked = 0;

            for album in albums:
                cursor.execute(f"SELECT * FROM {TABLE_ALBUMS} WHERE albumId == ?", (album._id, ))
                found = cursor.fetchone()
                if found is None:
                    cursor.execute(f"INSERT INTO {TABLE_ALBUMS} (albumId, title) VALUES (?, ?)", (album._id, album._title,))
                    inserted += 1
                else:
                    skipped += 1

                for item in album._items:    
                    cursor.execute(f"SELECT * FROM {TABLE_LINKS} WHERE albumId == ? AND itemId = ?", (album._id, item))
                    found = cursor.fetchone()
                    if found is None:
                        cursor.execute(f"INSERT INTO {TABLE_LINKS} (albumId, itemId) VALUES (?, ?)", (album._id, item,))
                        linked += 1

                total += 1
                if total % 100 == 0: 
                    Log.Write(f"{total} albums processed")

            self._connection.commit()
            Log.Write(f"{total} albums processed, {skipped} skipped, {inserted} inserted into '{TABLE_ALBUMS}', {linked} records added into '{TABLE_LINKS}'")
        
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't insert records: {err}")

        
