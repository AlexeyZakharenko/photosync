#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Required https://github.com/googleapis/google-api-python-client
#  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# How to set up API see https://developers.google.com/docs/api/quickstart/python
# Save config file as a google-client_secret.json to the private directory (private/ by default)

try: 
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.errors import HttpError
except ImportError as err:
    raise Exception("Google API modules not intalled. Please run 'pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


from pathlib import Path
from os import path
from datetime import datetime

from requests import get, post

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

    def __init__(self, privatedir):
        self._privatedir = path.normpath(privatedir)
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, CLIENT_SECRET_FILE)):
            raise Exception(f"Please set up Google Photos Library API accroding this manual: https://developers.google.com/docs/api/quickstart/python, create OAuth credentails and save JSON as {path.join(self._privatedir, CLIENT_SECRET_FILE)}")
        register(self.__close)

    def __close(self):
        if hasattr(self,"_service"):
            self._service.close()
            Log.Write(f"Disconnect from Google")

    def _connect(self):
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
            self._token = creds.token

            Log.Write(f"Connected to Google Service via API {API_NAME} {API_VERSION}")
        
        except HttpError as err:
            Log.Write(f"Can't connect to Google: {err}")

    @staticmethod
    def _getBody(start, end): 

        body = {
                "pageSize": "100",
        }
        
        # Add dates if required
        if start != None or end != None:
            if start == None:
                start = datetime.min.date()
            if end == None:
                end = datetime.max.date()

            body = {
                "pageSize": "100",
                "filters": {
                    "dateFilter": {
                        "ranges": [
                            {
                                "startDate": {
                                    "year": f"{start.year}",
                                    "month": f"{start.month}",
                                    "day": f"{start.day}"
                                },
                                "endDate": {
                                    "year": f"{end.year}",
                                    "month": f"{end.month}",
                                    "day": f"{end.day}"
                                }
                            }
                        ]
                    }
                }           
            }

        return body

    def _getItemsInfo(self, start=None, end=None):
        self._connect()
        result = []
        Log.Write(f"Getting items info from Google...")
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
                    result.append(Item.Item(item['id'], item['filename'], patchId=Google._getPatchId(item['filename'], item['mediaMetadata']['creationTime'])))
                    if len(result) % 1000 == 0:
                        Log.Write(f"Got info for {len(result)} items")

            Log.Write(f"Successfully got info for {len(result)} items")

        except HttpError as err:
            Log.Write(f"ERROR Can't get items info from Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")



        return result

    def _getAlbumsInfoByType(self, type, albums, items, start=None, end=None, excludeAlbums=None):
            n=0
            Log.Write(f"Getting {type} albums info from Google...")
            nextPageToken = None
            while nextPageToken != '':
                nextPageToken = '' if nextPageToken == None else nextPageToken

                if type == 'shared':
                    request = self._service.sharedAlbums().list(pageSize = 50, pageToken = nextPageToken).execute()
                    albumRecords = request.get('sharedAlbums', [])
                else:
                    request = self._service.albums().list(pageSize = 50, pageToken = nextPageToken).execute()
                    albumRecords = request.get('albums', [])

                nextPageToken = request.get('nextPageToken', '')

                for a in albumRecords:
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
                            if start != None and Google._getDateTime(ai['mediaMetadata']['creationTime']).date() < start.date():
                                continue;
                            if end != None and Google._getDateTime(ai['mediaMetadata']['creationTime']).date() > end.date():
                                continue;
                            if next((i for i in items if i.SrcId == ai['id']), None) is None:
                                items.append(Item.Item(ai['id'], ai['filename'], patchId=Google._getPatchId(ai['filename'], ai['mediaMetadata']['creationTime'])))

                            album.Items.append(ai['id'])        

                    # В исключениях
                    if excludeAlbums != None and album.Title in excludeAlbums:
                        continue;

                    if len(album.Items) > 0:        
                        albums.append(album)    

                    n += 1 
                    if n % 10 == 0:
                        Log.Write(f"Scan info for {n} {type} albums")

            if n % 10 != 0:
                Log.Write(f"Scan info for {n} {type} albums")

    def _getAlbumsInfo(self, items, start=None, end=None, excludeAlbums=None):
        self._connect()
        albums = []

        try:

            self._getAlbumsInfoByType('private', albums, items, start, end, excludeAlbums)
            self._getAlbumsInfoByType('shared', albums, items, start, end, excludeAlbums)

            Log.Write(f"Successfully got info for {len(albums)} albums")

        except HttpError as err:
            Log.Write(f"ERROR Can't get album info from Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")

        return albums


    @staticmethod
    def _getPatchId(filename, date):
        return f"{filename.lower()}:{Google._getSeconds(Google._getDateTime(date))}";

    @staticmethod
    def _getSeconds(dt):
        return int((dt-datetime(1970,1,1)).total_seconds())

    @staticmethod
    def _getDateTime(dateString):
        if dateString[-1:] == 'Z':
            return datetime.fromisoformat(dateString[:-1])
        else:
            return datetime.fromisoformat(dateString)

    def GetType(self):
        return f"Google ({path.join(self._privatedir, CLIENT_SECRET_FILE)})"

    def GetStatus(self):
        self._connect()
        Log.Write(self.GetType())

    def GetInfo(self, start=None, end=None, scope='all', excludeAlbums=None):

        items = []
        if scope == 'all' or scope == 'items':
            items = self._getItemsInfo(start, end)
            

        if scope == 'all' or scope == 'albums':
            albums = self._getAlbumsInfo(items, start, end, excludeAlbums)
        else:
            albums = []
        
        return (items, albums)

    def CheckItem(self, item, type='dst'):
        self._connect()
        id = item.DstId if type == 'dst' else item.SrcId; 
        try:
            itemInfo = self._service.mediaItems().get(mediaItemId = id).execute()
        except HttpError as err:
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")
            Log.Write(f"Missed item '{item.Filename} ({id})")
            return False

        return True

    def GetItem(self, item, cache):
        self._connect()
        try:
            itemInfo = self._service.mediaItems().get(mediaItemId = item.SrcId).execute()
            item.Created = Google._getDateTime(itemInfo['mediaMetadata']['creationTime'])
            if not itemInfo['mediaMetadata'].get('video',None) is None:
                if itemInfo['mediaMetadata']['video']['status'] != 'READY':
                    raise Exception(f"Invalid video status '{itemInfo['mediaMetadata']['video']['status']}'")
                dKey = "dv"
                item.Type='video'
            else:
                dKey = "d"
                item.Type='image'
            request = get(f"{itemInfo['baseUrl']}={dKey}")
            if not request.ok:
                raise Exception(f"{request.reason} ({request.status_code})")

            cache.Store(item.SrcId, request.content)
            Log.Write(f"Got item '{item.Filename}' {len(request.content)}b ({item.SrcId})")

        except HttpError as err:
            Log.Write(f"ERROR Can't get item '{item.Filename}' ({item.SrcId} {item.DstId}) from Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")
            return False

        except Exception as err:
            Log.Write(f"ERROR Can't get item '{item.Filename}' from Google: {err}")
            return False

        return True

    def _uploadMedia(self, content):

        upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
        size = len(content)

        startHeaders = {"Authorization": "Bearer " + self._token,
                "Content-Length": "0",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Content-Type": "application/octet-stream",
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Raw-Size": f"{size}"}

        response = post(upload_url, headers=startHeaders)
        if response.status_code != 200:
            raise Exception(f"Bad start upload status {response.status_code}")

        url = response.headers['X-Goog-Upload-URL']

        uploadHeaders = {"Authorization": "Bearer " + self._token,
                "Content-Length": f"{size}",
                "X-Goog-Upload-Command": "upload, finalize",
                "X-Goog-Upload-Offset": "0"}

        response = post(url, data=content, headers=uploadHeaders)
        if response.status_code != 200:
            raise Exception(f"Bad upload status {response.status_code}")

        return response.content.decode("utf-8")

    def PutItem(self, item, cache):
        self._connect()
        try:

            token = self._uploadMedia(cache.Get(item.SrcId))
            
            response = self._service.mediaItems().batchCreate(body={
                "newMediaItems": [
                    {
                        "simpleMediaItem": {
                            "fileName": item.Filename,
                            "uploadToken": token
                        }
                    }
                ]}).execute()


            if not response['newMediaItemResults'][0]['status']['message'] in ['Success', 'OK'] :
                raise Exception(f"Invalid response {response['newMediaItemResults'][0]['status']['message']}")

            item.DstId = response['newMediaItemResults'][0]['mediaItem']['id']

            Log.Write(f"Put item '{item.Filename}' ({item.DstId})")


        except HttpError as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")
            return False

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' to Google: {err}")
            return False

        finally:
            cache.Remove(item.SrcId)

        return True
    
    def PutAlbum(self, album):
        self._connect()
        try:

            response = self._service.albums().create(body={"album": {"title": album.Title}}).execute()
            album.DstId = response['id']
            Log.Write(f"Put album '{album.Title}' ({album.DstId})")

        except HttpError as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")
            return False

        except Exception as err:
            Log.Write(f"ERROR Can't put album '{album.Title}' to Google: {err}")
            return False


        return True

    def PutItemToAlbum(self, item, album):
        self._connect()
        try:
            self._service.albums().batchAddMediaItems(albumId=album.DstId, body={"mediaItemIds": [item.DstId]}).execute()
            Log.Write(f"Put item '{item.Filename}' into album '{album.Title}' ({item.DstId} -> {album.DstId})")

        except HttpError as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' into album '{album.Title}' to Google: {err}")
            if err.status_code == 429:
                raise Exception("Quota exceeded for Google service")
            return False

        except Exception as err:
            Log.Write(f"ERROR Can't put item '{item.Filename}' into album '{album.Title}' to Google: {err}")
            return False


        return True
