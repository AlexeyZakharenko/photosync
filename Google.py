#!/usr/bin/python
# -*- coding: UTF-8 -*-

# How to set up API see https://developers.google.com/docs/api/quickstart/python
# Save as a google-client_secret.json to the project's private directory

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

from pathlib import Path
from os import path, remove
from json import loads

import Log
import Item
import Album

CLIENT_SECRET_FILE = 'google-client_secret.json'
TOKEN_FILE = 'google-token.json'

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']


# Фильтр на полгода
BODY = {
    "filters": {
        "dateFilter": {
            "ranges": [
                {
                    "startDate": {
                        "year": 2022,
                        "month": 12,
                        "day": 1
                    },
                    "endDate": {
                        "year": 2022,
                        "month": 12,
                        "day": 31
                    }
                }
            ]
        }
    }        
}
BODY = {}

class Google:

    def __init__(self, privatedir):
        self._privatedir = privatedir
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, CLIENT_SECRET_FILE)):
            raise Exception(f"Please set up Google Photos Library API accroding this manual: https://developers.google.com/docs/api/quickstart/python, create OAuth credentails and save JSON as {path.join(self._privatedir, CLIENT_SECRET_FILE)}")

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

    def __del__(self):
        if hasattr(self,"_service"):
            self._service.close()
            Log.Write(f"Disconnect from Google service")

    def GetInfo(self):
        self.Connect()
        items = self.GetItemsInfo(body = BODY)
        albums = self.GetAlbumsInfo()
        Log.Write(f"Google service contains {len(items)} items and {len(albums)} albums")


    def GetItemsInfo(self, body = {}):
        self.Connect()

        #it = self._service.mediaItems().get(mediaItemId = 'AFK8nT5GkY5Nsw9i000PuXAZk4bcddCHWxaKJohdysvXz6q7abvvswG8R6jqchAKZ9xT7LzyvvZ8EMUMwbtneDjsW33YyN38ZA').execute()

        body["pageSize"] = 100
        result = []
        Log.Write(f"Getting items info from Google service...")
        try:
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

    def GetAlbumsInfo(self):
        self.Connect()
        result = []
        Log.Write(f"Getting albums info from Google service...")
        try:
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
                            "albumId": album._id,
                            "pageSize": 100,
                            "pageToken": nextAlbumToken
                        }).execute()

                        albumItems = albumRequest.get('mediaItems', [])
                        nextAlbumToken = albumRequest.get('nextPageToken', '')
                        for ai in albumItems:
                            album._items.append(ai['id'])        
                    result.append(album)    
                    if len(result) % 10 == 0:
                        Log.Write(f"Got info for {len(result)} albums")


            Log.Write(f"Successfully got info for {len(result)} albums")

        except HttpError as err:
            Log.Write(f"ERROR Can't get album info from Google service: {err}")


        return result