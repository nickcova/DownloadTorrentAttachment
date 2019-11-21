#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
from lib.mailFunctions import fetchnewmail
from lib.programSettings import ProgramSettings
import datetime

def main(argv=None):

    # Default configuration file path/filename
    configpath = "settings.cfg"

    # If no arguments are passed on to the function, use the command
    # line arguments
    if argv is None:
        argv = sys.argv

    # Get and check the command line arguments. Print usage if wrong
    # parameters are passed to the script.
    try:
        opts, args = getopt.getopt(argv[1:], "c:", ["config="])
    except getopt.GetoptError:
        print 'Error!!! Script usage is: "getMyTorrent.py [-c <configFile>]"'
        return -1

    for opt, arg in opts:
        if opt in ("-c", "--config"):
            configpath = arg
    
    print datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " GetMyTorrent V1.1 Starting..."
    # Create a 'settings' object.
    settings = ProgramSettings(configpath)
    result = fetchnewmail(settings)

    if result == 0:
        return 0

    return result

if __name__ == '__main__':
    sys.exit(main())
