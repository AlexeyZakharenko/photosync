#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Required https://github.com/googleapis/google-api-python-client

# How to set up API see https://developers.google.com/docs/api/quickstart/python
# Save config file as a google-client_secret.json to the private directory (private/ by default)

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

from pathlib import Path
from os import path
from datetime import datetime, timezone

from requests import get

from atexit import register

import Modules.Log as Log
import Modules.Item as Item
import Modules.Album as Album

CLIENT_SECRET_FILE = 'google-client_secret.json'
TOKEN_FILE = 'google-token.json'

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

class Google:

    def GetType(self):
        return f"Google ({path.join(self._privatedir, CLIENT_SECRET_FILE)})"

    def __init__(self, privatedir):
        self._privatedir = path.normpath(privatedir)
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, CLIENT_SECRET_FILE)):
            raise Exception(f"Please set up Google Photos Library API accroding this manual: https://developers.google.com/docs/api/quickstart/python, create OAuth credentails and save JSON as {path.join(self._privatedir, CLIENT_SECRET_FILE)}")
        register(self.__close)


    def Connect(self):
        if hasattr(self,"_service"):
            return
        try:
            creds = None
            # Get credentials
            if path.exists(path.join(self._privatedir, TOKEN_FILE)):
                creds = Credentials.from_authorized_user_file(path.join(self._privatedir, TOKEN_FILE), SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(path.join(self._privatedir, CLIENT_SECRET_FILE), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(path.join(self._privatedir, TOKEN_FILE), 'w') as token:
                    token.write(creds.to_json())

            self._service = build(API_NAME, API_VERSION,  credentials=creds, static_discovery=False)
            Log.Write(f"Connected to Google Service via API {API_NAME} {API_VERSION}")
        
        except HttpError as err:
            Log.Write(f"Can't connect to Google service: {err}")

    def __close(self):
        if hasattr(self,"_service"):
            self._service.close()
            Log.Write(f"Disconnect from Google service")

    def GetInfo(self):
        self.Connect()
        items = self.GetItemsInfo(body = {})
        albums = self.GetAlbumsInfo()
        Log.Write(f"Google service contains {len(items)} items and {len(albums)} albums")


    def _getBody(start, end):

        body = {
                "pageSize": 100,
        }
        
        # Add dates if required
        if start != None or end != None:
            if start == None:
                start = datetime.min.date()
            if end == None:
                end = datetime.max.date()

            body = {
                "pageSize": 100,
                "filters": {
                    "dateFilter": {
                        "ranges": [
                            {
                                "startDate": {
                                    "year": start.year,
                                    "month": start.month,
                                    "day": start.day
                                },
                                "endDate": {
                                    "year": end.year,
                                    "month": end.month,
                                    "day": end.day
                                }
                            }
                        ]
                    }
                }           
            }

        return body

    def GetItemsInfo(self, start=None, end=None):
        self.Connect()
        result = []
        Log.Write(f"Getting items info from Google service...")
        try:
            body = Google._getBody(start, end)
            nextPageToken = None
            n = 0
            while nextPageToken != '':
                nextPageToken = '' if nextPageToken == None else nextPageToken
                body["pageToken"] = nextPageToken
                request = self._service.mediaItems().search(body = body).execute()
                items = request.get('mediaItems', [])
                nextPageToken = request.get('nextPageToken', '')
                for item in items:
                    result.append(Item.Item(item['id'], item['filename']))
                    if len(result) % 1000 == 0:
                        Log.Write(f"Got info for {len(result)} items")

            Log.Write(f"Successfully got info for {len(result)} items")

        except HttpError as err:
            Log.Write(f"ERROR Can't get items info from Google service: {err}")


        return result

    def GetAlbumsInfo(self, start=None, end=None):
        self.Connect()
        result = []

        try:
            n=0;
            Log.Write(f"Getting private albums info from Google service...")
            nextPageToken = None
            while nextPageToken != '':
                nextPageToken = '' if nextPageToken == None else nextPageToken
                request = self._service.albums().list(pageSize = 50, pageToken = nextPageToken).execute()
                albums = request.get('albums', [])
                nextPageToken = request.get('nextPageToken', '')

                for a in albums:
                    album = Album.Album(a['id'], a['title'])

                    # Ask for photos in album
                    nextAlbumToken = None
                    while nextAlbumToken != '':

                        nextAlbumToken = '' if nextAlbumToken == None else nextAlbumToken
                        albumRequest = self._service.mediaItems().search(body = {
                            "albumId": album.SrcId,
                            "pageSize": 100,
                            "pageToken": nextAlbumToken
                        }).execute()


                        albumItems = albumRequest.get('mediaItems', [])
                        nextAlbumToken = albumRequest.get('nextPageToken', '')
                        for ai in albumItems:
                            album.Items.append(ai['id'])        
                    result.append(album)   
                    n += 1 
                    if n % 10 == 0:
                        Log.Write(f"Got info for {n} private albums")

            if n % 10 != 0:
                Log.Write(f"Got info for {n} private albums")

            n=0
            Log.Write(f"Getting shared albums info from Google service...")
            nextPageToken = None
            while nextPageToken != '':
                nextPageToken = '' if nextPageToken == None else nextPageToken
                request = self._service.sharedAlbums().list(pageSize = 50, pageToken = nextPageToken).execute()
                albums = request.get('sharedAlbums', [])
                nextPageToken = request.get('nextPageToken', '')

                for a in albums:
                    album = Album.Album(a['id'], a['title'])

                    # Ask for photos in album
                    nextAlbumToken = None
                    while nextAlbumToken != '':
                        nextAlbumToken = '' if nextAlbumToken == None else nextAlbumToken
                        albumRequest = self._service.mediaItems().search(body = {
                            "albumId": album.SrcId,
                            "pageSize": 100,
                            "pageToken": nextAlbumToken
                        }).execute()
                        albumItems = albumRequest.get('mediaItems', [])
                        nextAlbumToken = albumRequest.get('nextPageToken', '')
                        for ai in albumItems:
                            album.Items.append(ai['id'])        
                    result.append(album)    
                    n += 1
                    if n % 10 == 0:
                        Log.Write(f"Got info for {n} shared albums")
            if n % 10 != 0:
                Log.Write(f"Got info for {n} shared albums")

            Log.Write(f"Successfully got info for {len(result)} albums")

        except HttpError as err:
            Log.Write(f"ERROR Can't get album info from Google service: {err}")


        return result

    def _getDateTime(dateString):
        if dateString[-1:] == 'Z':
            return datetime.fromisoformat(dateString[:-1])
            #return dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        else:
            return datetime.fromisoformat(dateString)

    def GetItem(self, item, cache):
        self.Connect()
        try:
            itemInfo = self._service.mediaItems().get(mediaItemId = item.SrcId).execute()
            item.Created = Google._getDateTime(itemInfo['mediaMetadata']['creationTime'])
            if not itemInfo['mediaMetadata'].get('video',None) is None:
                if itemInfo['mediaMetadata']['video']['status'] != 'READY':
                    raise Exception(f"Invalid video status '{itemInfo['mediaMetadata']['video']['status']}'")
                dKey = "dv"
            else:
                dKey = "d"
            request = get(f"{itemInfo['baseUrl']}={dKey}")
            if not request.ok:
                raise Exception(f"{request.reason} ({request.status_code})")

            cache.Store(item.SrcId, request.content)
            Log.Write(f"Got item '{item.Filename}' {len(request.content)}b ({item.SrcId})")

        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.Filename}' from Google service: {err}")
            return False

        return True

