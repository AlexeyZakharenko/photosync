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

    def GetDBFile(self):
        return self._filename

    def __close(self):
        if hasattr(self,"_connection"):
            self._connection.close()
            Log.Write(f"Disconnect from SQLite DB '{self._filename}'")

    def _connect(self):
        if not hasattr(self,"_connection"):
            self._connection = sqlite3.connect(self._filename)
            Log.Write(f"Connect to SQLite DB '{self._filename}'")

        self._checkItemsTable()
        self._checkAlbumsTable()
        self._checkLinksTable()

    def _checkItemsTable(self):
        cursor = self._connection.cursor()        
        cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{TABLE_ITEMS}'")        
        record = cursor.fetchone()
        if record[0] == 0:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ITEMS}(
srcId TEXT PRIMARY KEY,
patchId TEXT UNIQUE,
filename TEXT UNIQUE,
dstId TEXT UNIQUE,
sync INTEGER)
""")
            self._connection.commit()
            Log.Write(f"Table '{TABLE_ITEMS}' created")
        cursor.execute(f"SELECT COUNT(*) AS CNTREC FROM pragma_table_info('{TABLE_ITEMS}') WHERE name='patchId'")
        record = cursor.fetchone()
        if record[0] == 0:
            cursor.execute(f"ALTER TABLE {TABLE_ITEMS} ADD patchId TEXT")
            self._connection.commit()
            raise Exception(f"Table '{TABLE_ITEMS}' updated. Please run 'get' to complete upgrade.")

    def _checkAlbumsTable(self):
        cursor = self._connection.cursor()        
        cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{TABLE_ALBUMS}'")        
        record = cursor.fetchone()
        if record[0] == 0:
            self._connection.commit()
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_ALBUMS}(
srcId TEXT PRIMARY KEY,
title TEXT UNIQUE,
dstId TEXT UNIQUE,
sync INTEGER)""")
            self._connection.commit()
            Log.Write(f"Table '{TABLE_ALBUMS}' created")

    def _checkLinksTable(self):
        cursor = self._connection.cursor()        
        cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{TABLE_LINKS}'")        
        record = cursor.fetchone()
        if record[0] == 0:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_LINKS}(
albumId TEXT NOT NULL,
itemId TEXT NOT NULL,
sync INTEGER NOT NULL)
""")
            self._connection.commit()
            Log.Write(f"Table '{TABLE_LINKS}' created")

    def CreateDB(self):
        self._connect()
        self._checkItemsTable()
        self._checkAlbumsTable()
        self._checkLinksTable()

    def DeleteDB(self):
        self._connect()
        cursor = self._connection.cursor()   
        for table in [TABLE_LINKS, TABLE_ALBUMS, TABLE_ITEMS]:     
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            self._connection.commit()
            Log.Write(f"Table '{table}' deleted")

    def Dump(self, scope='all'):
        if scope == 'all' or scope =='items':
            self._dumpTable(TABLE_ITEMS)
        if scope == 'all' or scope =='albums':
            self._dumpTable(TABLE_ALBUMS)
        if scope == 'all' or scope =='links':
            self._dumpTable(TABLE_LINKS)

    def _dumpTable(self,table):
        self._connect()
        jsonFile = f"{self._filename}-{table}.json"
        cursor = self._connection.cursor()   
        cursor.execute(f"SELECT * FROM {table}")
        try:
            with open(jsonFile, mode='wt', encoding='utf-8') as json_data:
                print(cursor.fetchall(), file=json_data)

            Log.Write(f"Table '{table}' from '{self._filename}' dumped to '{jsonFile}'")

        except Exception as e:
            Log.Write(f"ERROR Can't dump table '{table}' from '{self._filename}' to '{jsonFile}': {e}")

    def GetStatus(self):
        self._connect()
        cursor = self._connection.cursor()  

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ITEMS}")
        items = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ITEMS}")
        items = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ITEMS} WHERE sync != 0")
        itemsDone = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ALBUMS}")
        albums = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ALBUMS} WHERE sync != 0")
        albumsDone = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_LINKS}")
        links = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_LINKS} WHERE sync != 0")
        linksDone = cursor.fetchone()
        Log.Write(f"Table info: '{TABLE_ITEMS}':{items[0]}/{itemsDone[0]}, '{TABLE_ALBUMS}':{albums[0]}/{albumsDone[0]}, '{TABLE_LINKS}':{links[0]}/{linksDone[0]}")

    def UpdateItemsInfo(self,items):
        self._connect()
        Log.Write(f"Inserting {len(items)} records into '{TABLE_ITEMS}'...")
        try:
            cursor = self._connection.cursor()
            total = 0
            skipped = 0
            inserted = 0
            upgraded = 0

            for item in items:

                cursor.execute(f"SELECT srcId, patchId FROM {TABLE_ITEMS} WHERE srcId = ?", (item.SrcId,))
                found = cursor.fetchone()
                if found is None:


                    # check patchId    
                    cursor.execute(f"SELECT filename, srcId FROM {TABLE_ITEMS} WHERE patchId == ? COLLATE NOCASE", (item.PatchId,))
                    foundPatchId = cursor.fetchone()
                    if not foundPatchId is None:
                        Log.Write(f"WARNING: Same patchId for item {item.Filename} -> {foundPatchId[0]},  {item.SrcId} -> {foundPatchId[1]}")
                        continue


                    # generate unique file name
                    (name, ext) = path.splitext(item.Filename)
                    n = 0
                    checkFilename = True
                    while checkFilename:
                        cursor.execute(f"SELECT * FROM {TABLE_ITEMS} WHERE filename == ? COLLATE NOCASE", (item.Filename,))
                        found = cursor.fetchone()
                        if not found is None:
                            n += 1
                            item.Filename =f"{name}_{n}{ext}"
                        else:
                            checkFilename = False

                    cursor.execute(f"INSERT INTO {TABLE_ITEMS} (srcId, filename, patchId, sync) VALUES (?, ?, ?, ?)", (item.SrcId, item.Filename, item.PatchId, 0,))
                    inserted += 1
                else:
                    if found[1] is None and not item.PatchId is None :
                        upgraded += 1
                        cursor.execute(f"UPDATE {TABLE_ITEMS} SET patchId = ? WHERE srcId = ?", (item.PatchId, item.SrcId, ))

                    skipped += 1

                total += 1
                if total % 1000 == 0: 
                    Log.Write(f"{total} records processed")

            self._connection.commit()
            
            upgraded_info = (f", {upgraded} upgraded") if upgraded > 0 else ""
            Log.Write(f"{total} records processed, {skipped} skipped, {inserted} inserted{upgraded_info} into '{TABLE_ITEMS}'")
        
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

                    # generate unique album name
                    albumTitle = album.Title;
                    n = 0
                    checkAlbum = True
                    while checkAlbum:
                        cursor.execute(f"SELECT * FROM {TABLE_ALBUMS} WHERE title == ? COLLATE NOCASE", (album.Title,))
                        found = cursor.fetchone()
                        if not found is None:
                            n += 1
                            album.Title =f"{albumTitle}_{n}"
                        else:
                            checkAlbum = False

                    cursor.execute(f"INSERT INTO {TABLE_ALBUMS} (srcId, title, sync) VALUES (?, ?, ?)", (album.SrcId, album.Title, 0,))
                    inserted += 1
                else:
                    skipped += 1

                for item in album.Items:    

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

    def GetItemsForCheck(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT srcId, dstId, filename, sync FROM {TABLE_ITEMS}")
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Item.Item(srcId=record[0], dstId=record[1], filename=record[2], sync=record[3]))

            Log.Write(f"Got {len(result)} items to check")
        
        except Exception as err:
            Log.Write(f"ERROR Can't get records: {err}")
        
        return result

    def GetAlbumsForSync(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT srcId, dstId, title, sync FROM {TABLE_ALBUMS} WHERE sync = ?", (0,))
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Album.Album(srcId=record[0], dstId=record[1], title=record[2], sync=record[3]))

            Log.Write(f"Got {len(result)} albums to check")
        
        except Exception as err:
            Log.Write(f"ERROR Can't get records: {err}")
        
        return result

    def GetAlbumsForCheck(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT srcId, dstId, title, sync FROM {TABLE_ALBUMS}")
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Album.Album(srcId=record[0], dstId=record[1], title=record[2], sync=record[3]))

            Log.Write(f"Got {len(result)} albums to check")
        
        except Exception as err:
            Log.Write(f"ERROR Can't get records: {err}")
        
        return result

    def GetLinksForCheck(self):
        self._connect()
        result = []
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT albumId, itemId, sync FROM {TABLE_LINKS}")
            records = cursor.fetchall()
            if not records is None:
                for record in records:
                    result.append(Link.Link(albumId=record[0], itemId=record[1], sync=record[2]))

            Log.Write(f"Got {len(result)} links to check")
        
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

            return Album.Album(albumId, record[0], record[1] if record[2] != 0 else None, record[2])        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get album '{albumId}' from table: {err}")
        
        return None 

    def GetItem(self, itemId):
        self._connect()
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT filename, dstId, sync FROM {TABLE_ITEMS} WHERE srcId = ?", (itemId,))
            record = cursor.fetchone()
            if record is None:
                raise Exception(f"Not found")

            return Item.Item(itemId, record[0], record[1] if record[2] != 0 else None)        
        
        except Exception as err:
            Log.Write(f"ERROR Can't get item '{itemId}' from table: {err}")
        
        return None 

    def MarkItemSync(self, item, sync=1):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_ITEMS} SET dstId = ?, sync = ? WHERE srcId = ?", (item.DstId, sync, item.SrcId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't set item {item.SrcId} sync to '{sync}': {err}")
            return False

        return True

    def MarkAlbumSync(self, album, sync=1):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_ALBUMS} SET dstId = ?, sync = ? WHERE srcId = ?", (album.DstId, sync, album.SrcId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't set album {album.SrcId} sync to '{sync}': {err}")
            return False
        return True

    def MarkLinkSync(self, link, sync=1):
        self._connect()
        cursor = self._connection.cursor()
        try:
            cursor.execute(f"UPDATE {TABLE_LINKS} SET sync = ? WHERE albumId = ? AND itemId = ?", (sync, link.AlbumId, link.ItemId, ))
            self._connection.commit()
        except Exception as err:
            self._connection.rollback()
            Log.Write(f"ERROR Can't set link {link.AlbumId} - {link.ItemId} sync to '{sync}': {err}")
            return False

        return True

    def Clean(self, scope = 'all', excludeAlbums=None):
        self._connect()
        cursor = self._connection.cursor()
        if excludeAlbums != None:
            for albumTitle in excludeAlbums:
                cursor.execute(f"SELECT srcId FROM {TABLE_ALBUMS} WHERE title = ?", (albumTitle,))
                records = cursor.fetchmany(2)
                if len(records) == 0:
                    continue;
                if len(records) > 1:
                    raise Exception(f"Album {albumTitle} has more than one record at table {TABLE_ALBUMS}")
                albumId = records[0][0];
                cursor.execute(f"DELETE FROM {TABLE_LINKS} WHERE albumId = ?", (albumId,))
                cursor.execute(f"DELETE FROM {TABLE_ALBUMS} WHERE srcId = ?", (albumId,))
                self._connection.commit()
                Log.Write(f"Delete info for album '{albumTitle}'")
                

        else:
            if scope == 'all' or scope =='items':
                cursor.execute(f"UPDATE {TABLE_ITEMS} SET sync = ?, dstId = ?", (0, None, ))
                Log.Write(f"Clean sync flags in table {TABLE_ITEMS}")
            if scope == 'all' or scope =='albums':
                cursor.execute(f"UPDATE {TABLE_ALBUMS} SET sync = ?, dstId = ?", (0, None, ))
                Log.Write(f"Clean sync flags in table {TABLE_ALBUMS}")
                cursor.execute(f"UPDATE {TABLE_LINKS} SET sync = ?", (0, ))
                Log.Write(f"Clean sync flags in table {TABLE_LINKS}")

        self._connection.commit()
