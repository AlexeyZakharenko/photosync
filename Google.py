#!/usr/bin/python
# -*- coding: UTF-8 -*-

# How to set up API see https://developers.google.com/docs/api/quickstart/python
# Save as a google-client_secret.json to the project's private directory

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError


import Log
from pathlib import Path
from os import path, remove



CLIENT_SECRET_FILE = 'google-client_secret.json'
TOKEN_FILE = 'google-token.json'

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']


class Google(object):

    def __init__(self, privatedir):
        self._privatedir = privatedir
        Path(self._privatedir).mkdir(parents=True, exist_ok=True)
        if not path.exists(path.join(self._privatedir, CLIENT_SECRET_FILE)):
            raise Exception(f"Please set up Google Photos Library API accroding this manual: https://developers.google.com/docs/api/quickstart/python, create OAuth credentails and save its JSON as {path.join(self._privatedir, CLIENT_SECRET_FILE)}")
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
        albums = self._service.albums()
        Log.Write(f"Ok {albums}")