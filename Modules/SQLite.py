#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sqlite3

from atexit import register

from os import path
from pathlib import Path

import Modules.Item as Item
import Modules.Album as Album
import Modules.Link as Link

import Modules.Log as Log

TABLE_ITEMS = 'items'
TABLE_ALBUMS = 'albums'
TABLE_LINKS = 'links'

class DB(object):

    def __init__(self, dbfile):
        dir = path.split(path.abspath(dbfile))
        Path(dir[0]).mkdir(parents=True, exist_ok=True)
        self._filename = path.normpath(dbfile)
        register(self.__close)

    def _connect(self):
        if not hasattr(self,"_connection"):
            self._connection = sqlite3.connect(self._filename)
            Log.Write(f"Connect to SQLite DB '{self._filename}'")

    def __close(self):
        if hasattr(self,"_connection"):
            self._connection.close()
            Log.Write(f"Disconnect from SQLite DB '{self._filename}'")

    def CreateDB(self):
        self._connect()
        cursor = self._connection.cursor()        

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ITEMS}(
   srcId TEXT PRIMARY KEY,
   filename TEXT,
   dstId TEXT,
   sync INTEGER)
    """)
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ITEMS}' created")

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ALBUMS}(
   srcId TEXT PRIMARY KEY,
   title TEXT,
   dstId TEXT,
   sync INTEGER)""")
        self._connection.commit()
        Log.Write(f"Table '{TABLE_ALBUMS}' created")

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_LINKS}(
   albumId TEXT NOT NULL,
   itemId TEXT NOT NULL,
   sync INTEGER NOT NULL)
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
        items = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ITEMS} WHERE sync = 1")
        itemsDone = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ALBUMS}")
        albums = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_ALBUMS} WHERE sync = 1")
        albumsDone = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_LINKS}")
        links = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) AS NRECORDS FROM {TABLE_LINKS} WHERE sync = 1")
        linksDone = cursor.fetchall()
        Log.Write(f"Table info: '{TABLE_ITEMS}':{items[0][0]}/{itemsDone[0][0]}, '{TABLE_ALBUMS}':{albums[0][0]}/{albumsDone[0][0]}, '{TABLE_LINKS}':{links[0][0]}/{linksDone[0][0]}")

    def UpdateItemsInfo(self,items):
        self._connect()
        Log.Write(f"Inserting {len(items)} records into '{TABLE_ITEMS}'...")
        try:
            cursor = self._connection.cursor()
            total = 0
            skipped = 0
            inserted = 0

            for item in items:

                cursor.execute(f"SELECT * FROM {TABLE_ITEMS} WHERE srcId = ?", (item.SrcId,))
                found = cursor.fetchone()
                if found is None:
                    cursor.execute(f"INSERT INTO {TABLE_ITEMS} (srcId, filename, sync) VALUES (?, ?, ?)", (item.SrcId, item.Filename, 0,))
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
        
    def UpdateAlbumsInfo(self,albums):
        self._connect()
        Log.Write(f"Inserting {len(albums)} records into '{TABLE_ALBUMS}'...")
        try:
            cursor = self._connection.cursor()
            total = 0
            skipped = 0
            inserted = 0
            linked = 0;

            for album in albums:
                cursor.execute(f"SELECT * FROM {TABLE_ALBUMS} WHERE srcId == ?", (album.SrcId,))
                found = cursor.fetchone()
                if found is None:
                    cursor.execute(f"INSERT INTO {TABLE_ALBUMS} (srcId, title, sync) VALUES (?, ?, ?)", (album.SrcId, album.Title, 0,))
                    inserted += 1
                else:
                    skipped += 1

                for item in album.Items:    

                    # Looking for items table
                    cursor.execute(f"SELECT * FROM {TABLE_ITEMS} WHERE srcId = ?", (item,))
                    found = cursor.fetchone()
                    if found is None:
                        continue

                    cursor.execute(f"SELECT * FROM {TABLE_LINKS} WHERE albumId = ? AND itemId = ?", (album.SrcId, item,))
                    found = cursor.fetchone()
                    if found is None:
                        cursor.execute(f"INSERT INTO {TABLE_LINKS} (albumId, itemId, sync) VALUES (?, ?, ?)", (album.SrcId, item, 0,))
                        linked += 1

                total += 1
                if total % 100 == 0: 
                    Log.Write(f"{total} albums processed")

            self._connection.commit()
            Log.Write(f"{total} albums processed, {skipped} skipped, {inserted} inserted into '{TABLE_ALBUMS}', {linked} records added into '{TABLE_LINKS}'")
        
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't insert records: {err}")

    def GetItemsForSync(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT srcId, filename FROM {TABLE_ITEMS} WHERE sync = ?", (0,))
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Item.Item(record[0],record[1]))

            Log.Write(f"Got {len(result)} items to sync")
        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get records: {err}")
        
        return result

    def GetLinksForSync(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT albumId, itemId FROM {TABLE_LINKS} WHERE sync = ?", (0,))
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Link.Link(record[0],record[1]))

            Log.Write(f"Got {len(result)} links to sync")
        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get records: {err}")
        
        return result

    def GetAlbum(self, albumId):
        self._connect()
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT title, dstId, sync FROM {TABLE_ALBUMS} WHERE srcId = ?", (albumId,))
            record = cursor.fetchone()
            if record is None:
                raise Exception(f"Not found")

            return Album.Album(albumId, record[0], record[1] if record[2] == 1 else None)        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get album '{albumId}': {err}")
        
        return None 

    def GetItem(self, itemId):
        self._connect()
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT filename, dstId, sync FROM {TABLE_ITEMS} WHERE srcId = ?", (itemId,))
            record = cursor.fetchone()
            if record is None:
                raise Exception(f"Not found")

            return Item.Item(itemId, record[0], record[1] if record[2] == 1 else None)        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get item '{itemId}': {err}")
        
        return None 

    def MarkItemSync(self, item):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_ITEMS} SET dstId = ?, sync = ? WHERE srcId = ?", (item.DstId, 1, item.SrcId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't mark item {item.SrcId} as sync: {err}")
            return False

        return True


    def MarkAlbumSync(self, album):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_ALBUMS} SET dstId = ?, sync = ? WHERE srcId = ?", (album.DstId, 1, album.SrcId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't mark album {album.SrcId} as sync: {err}")
            return False
        return True
        

    def MarkLinkSync(self, link):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_LINKS} SET sync = ? WHERE albumId = ? AND itemId = ?", (1, link.AlbumId, link.ItemId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't mark link {link.AlbumId} - {link.ItemId} as sync: {err}")
            return False

        return True

    def Clean(self):
        self._connect()
        cursor = self._connection.cursor()
        cursor.execute(f"UPDATE {TABLE_ITEMS} SET sync = ?, dstId = ?", (0, None, ))
        cursor.execute(f"UPDATE {TABLE_ALBUMS} SET sync = ?, dstId = ?", (0, None, ))
        cursor.execute(f"UPDATE {TABLE_LINKS} SET sync = ?", (0, ))
        self._connection.commit()
        Log.Write(f"All sync flags in tables are cleaned")