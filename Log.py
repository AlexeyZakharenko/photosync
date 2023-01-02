#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime

def Write(string):
    print(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\t{string}")