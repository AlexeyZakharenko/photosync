#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime

def Write(string, date=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),  end='\n'):
    if date != None:
        date = f"{date}\t"
    else:
        date = ''
        
    print(f"{date}{string}", end=end)