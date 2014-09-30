#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
import lib.mailFunctions as MF
import lib.programSettings
from datetime import datetime

def main(argv=None):

    # Default configuration file path/filename
    configPath = "settings.cfg"

    # If no arguments are passed on to the function, use the command
    # line arguments
    if argv is None:
        argv = sys.argv

    # Get and check the command line arguments. Print usage if wrong
    # parameters are passed to the script.
    try:
        opts, args = getopt.getopt(argv[1:],"c:",["config="])
    except getopt.GetoptError:
        print 'Error!!! Script usage is: "getMyTorrent.py [-c <configFile>]"'
        return -1

    for opt, arg in opts:
        if opt in ("-c", "--config"):
            configPath = arg
    
    print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " GetMyTorrent V1.0 Starting..."
    # Create a 'settings' object.
    settings = lib.programSettings.ProgramSettings(configPath)
    result = MF.fetchNewMail(settings)

    if result == 0:
        return 0

    return -1

if __name__ == '__main__':
    sys.exit(main())
