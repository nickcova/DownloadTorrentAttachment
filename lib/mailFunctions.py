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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

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

    # Call the Gmail API and bring unread emails in the Inbox
    unread_msgs = service.users().messages().list(userId='me', labelIds='INBOX', q='is:unread').execute()

    if not unread_msgs.get('messages'):
        print('No unread messages found. Exiting.')
    else:
        file_downloaded = False
        attachment_filename = ""

        msg = unread_msgs.get('messages')[0]
        msg_id = msg.get('id')
        msg_details = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        for part in msg_details['payload']['parts']:
            # If the attachment is a torrent file, download it
            if "application/x-bittorrent" == part['mimeType']:
                print("Found a .torrent file!") 

                try:                    
                    attachment = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=part['body']['attachmentId']).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                    store_dir = settings.downloadPath
                    path = ''.join([store_dir, part['filename']])
                    attachment_filename = part['filename']

                    f = open(path, 'w')
                    f.write(file_data)
                    f.close()

                    file_downloaded = True

                except errors.HttpError, error:
                    print ('An error occurred: %s' % error)
            else:
                print('Part has no attachment, skipping...')

        # Mark message as READ
        msg_labels = {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}
        service.users().messages().modify(userId='me', id=msg_id, body=msg_labels).execute()        

        if file_downloaded:
            send_notification(service, settings, attachment_filename)

    return 0


def send_notification(service, settings, filename):
    notification_message = create_notification_message(settings, filename)

    if notification_message is not None:
        sentMsg = send_message(service, "me", notification_message)
        print(sentMsg)


def create_notification_message(settings, filename):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    filename: The name of the torrent file that was downloaded.

    Returns:
    An object containing a base64url encoded email object.
    """
    
    message = MIMEMultipart("related")
    message["to"] = settings.recipient
    message["from"] = settings.login
    message["subject"] = "Torrent File Downloaded"
    message.preamble = "This is a multi-part message in MIME format."

    msgAlternative = MIMEMultipart('alternative')
    message.attach(msgAlternative)

    plain_text = "File '" + filename + "' downloaded."

    html_file = open("html/email_notification.html","r")
    html = html_file.read()
    html = html.replace("___ATTACHMENT___", filename)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plain_text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msgAlternative.attach(part1)
    msgAlternative.attach(part2)

    fp = open(settings.okImagePath, 'rb')
    msgimage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgimage.add_header('Content-ID', '<image1>')
    message.attach(msgimage)

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
