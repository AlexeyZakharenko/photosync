#!/usr/bin/python
# -*- coding: UTF-8 -*-

if __name__ != '__main__':
    print("Please run as main module")

import Command

try:
    Command.Invoke()

except Exception as err:
    print("Error: {}".format(err))
