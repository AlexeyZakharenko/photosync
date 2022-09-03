#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime

def Write(string):
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"{now}\t{string}")