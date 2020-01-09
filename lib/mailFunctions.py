# -*- coding: utf-8 -*-
from __future__ import print_function
from _ssl import SSLError
import os
import imaplib
import email
import re
import datetime
import smtplib

from apiclient import errors
import base64
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def istorrentfile(filename):
    """
    Checks if a file has a '.torrent' extension. A regular
    expression is used to validate
    """
    #TODO Is this still necessary?
    expression = re.compile(r".+\.torrent")
    if expression.match(filename) is not None:
        return True
    return False


def fetchnewmail(settings):
    """
    Logs into email account, checks for new messages,
    downloads latest new message and checks for attachments.
    If an attachment is found, it is downloaded into the
    specified directory.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('credentials/token.pickle'):
        with open('credentials/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('credentials/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    unread_msgs = service.users().messages().list(userId='me', labelIds='INBOX', q='is:unread').execute()

    if not unread_msgs.get('messages'):
        print('No unread messages found')
    else:
        msg = unread_msgs.get('messages')[0]
        msg_id = msg.get('id')
        msg_details = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        for part in msg_details['payload']['parts']:
            if "application/x-bittorrent" == part['mimeType']:
                print("Found a .torrent file!") 

                try:                    
                    attachment = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=part['body']['attachmentId']).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                    store_dir = settings.downloadPath
                    path = ''.join([store_dir, part['filename']])

                    f = open(path, 'w')
                    f.write(file_data)
                    f.close()
                except errors.HttpError, error:
                    print ('An error occurred: %s' % error)
            else:
                print('Part has no attachment, skipping...')

        # Mark message as READ
        msg_labels = {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}
        service.users().messages().modify(userId='me', id=msg_id, body=msg_labels).execute()        

    return 0


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_string())}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print ("Message Id: %s" % message["id"])
        return message
    except errors.HttpError, error:
        print ("An error occurred: %s" % error)


def sendsmtpmail(settings, emailtype, text):
    """
    Type 0 means 'OK'
    Type 1 means 'Warning'
    Type -1 means 'Error'
    """
    #TODO Is this still necessary?
    # Create the root message and fill in the from, to, and subject headers
    msgroot = email.MIMEMultipart.MIMEMultipart('related')
    msgroot['Subject'] = 'Raspberry Pi Notification'
    msgroot['From'] = settings.login
    msgroot['To'] = settings.recipient
    msgroot.preamble = 'This is a multi-part message in MIME format.'
    
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgalternative = email.MIMEMultipart.MIMEMultipart('alternative')
    msgroot.attach(msgalternative)
    
    # We reference the image in the IMG SRC attribute by the ID we give it below
    #msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
    #msgalternative.attach(msgText)
    
    if emailtype == 0:
        msgtext = email.MIMEText.MIMEText('Received attachment ('+text+") downloaded successfully at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        msgalternative.attach(msgtext)
        
        msgtext = email.MIMEText.MIMEText('<table width=600><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Received attachment ('+text+") downloaded succesfully at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')+"</td></tr></table>", "html")
        msgalternative.attach(msgtext)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_ok.jpg', 'rb')
        msgimage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgimage.add_header('Content-ID', '<image1>')
        msgroot.attach(msgimage)
        
    elif emailtype == 1:
        msgtext = email.MIMEText.MIMEText('Warning: '+text+" (at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')+')')
        msgalternative.attach(msgtext)
        
        msgtext = email.MIMEText.MIMEText('<table><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Warning: '+text+" (at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")</td></tr></table>", "html")
        msgalternative.attach(msgtext)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_warn.jpg', 'rb')
        msgimage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgimage.add_header('Content-ID', '<image1>')
        msgroot.attach(msgimage)
        
    elif emailtype == -1:
        msgtext = email.MIMEText.MIMEText('Error: '+text+" (at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")")
        msgalternative.attach(msgtext)
        
        msgtext = email.MIMEText.MIMEText('<table width=600><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Error: '+text+" (at "+datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")</td></tr></table>", "html")
        msgalternative.attach(msgtext)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_error.jpg', 'rb')
        msgimage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgimage.add_header('Content-ID', '<image1>')
        msgroot.attach(msgimage)

    # Send the email (this example assumes SMTP authentication is required)
    smtp = smtplib.SMTP(settings.smtpServer, settings.smtpPort)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(settings.login.split('@')[0], settings.password)
    smtp.sendmail(settings.login, settings.recipient, msgroot.as_string())
    smtp.quit()
