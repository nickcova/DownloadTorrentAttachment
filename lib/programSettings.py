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
            self._imapServer = None
            self._smtpServer = None
            self._smtpPort = None
            self._login = None
            self._password = None
            self._recipient = None
            self._downloadPath = None
        else:
            # Read the configuration file
            tree = et.parse(fileName)
            root = tree.getroot()
            # Set the object`s properties
            self._imapServer = root.find("imapServer").text
            self._smtpServer = root.find("smtpServer").text
            self._smtpPort = root.find("smtpServerPort").text
            self._login = root.find("login").text
            self._password = root.find("password").text
            self._recipient = root.find("recipient").text
            self._downloadPath = root.find("downloadLocation").text
    
    @property
    def imapServer(self):
        """ The IMAP Server address to be used of e-mail reception. """
        return self._imapServer
    
    @property
    def smtpServer(self):
        """ The SMTP Server address to be used to send e-mails """
        return self._smtpServer
    
    @property
    def smtpPort(self):
        """ The port to use when connecting to the SMTP server """
        return self._smtpPort
    
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
    def downloadPath(self):
        """ The system path where attached files from e-mails will be downloaded """
        return self._downloadPath