# -*- coding: utf-8 -*-
import xml.etree.ElementTree as et

class ProgramSettings(object):
    """
    Object containing the settings of the program
    """
    
    def __init__(self, fileName):
        """
        Class constructor
        """
        if fileName == '':
            self._login = None
            self._password = None
            self._recipient = None
            self._tokenPicklePath = None
            self._credentialsPath = None
            self._downloadPath = None
            self._okImagePath = None
        else:
            # Read the configuration file
            tree = et.parse(fileName)
            root = tree.getroot()
            # Set the object`s properties
            #self._login = root.find("login").text
            #self._password = root.find("password").text
            self._login = None
            self._password = None
            self._recipient = root.find("recipient").text
            self._tokenPicklePath = root.find("tokenPicklePath").text
            self._credentialsPath = root.find("credentialsPath").text
            self._downloadPath = root.find("downloadLocation").text
            self._okImagePath = root.find("okImageLocation").text
       
    @property
    def login(self):
        """ The e-mail address to be used to sign in into the SMTP/IMAP servers """
        return self._login
    
    @property
    def password(self):
        """ The password to be used to sign in into the SMTP/IMAP servers """
        return self._password
    
    @property
    def recipient(self):
        """ The e-mail address that will be used to filter received messages. This same address
        will be used in the 'To:' field of sent e-mails """
        return self._recipient

    @property
    def tokenPicklePath(self):
        """ The path to the token.pickle file """
        return self._tokenPicklePath

    @property
    def credentialsPath(self):
        """ The path to the credentials file """
        return self._credentialsPath
    
    @property
    def downloadPath(self):
        """ The system path where attached files from e-mails will be downloaded """
        return self._downloadPath

    @property
    def okImagePath(self):
        """ The system path of the attached image for notification emails """
        return self._okImagePath