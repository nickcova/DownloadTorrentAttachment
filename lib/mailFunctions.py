# -*- coding: utf-8 -*-
from _ssl import SSLError
import os
import imaplib
import email
import re
import socket

from datetime import datetime


def isTorrentFile(filename):
    """
    Checks if a file has a '.torrent' extension. A regular
    expression is used to validate
    """
    expression = re.compile(r".+\.torrent")
    if expression.match(filename) is not None:
        return True
    return False


def fetchNewMail(settings):
    """
    Logs into email account, checks for new messages,
    downloads latest new message and checks for attachments.
    If an attachment is found, it is downloaded into the
    specified directory.
    """

    try:
        mail = imaplib.IMAP4_SSL(settings.imapServer)
        print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Connecting to " + settings.imapServer + "..."
        mail.login(settings.login, settings.password)
        mail.select("inbox")  # connect to "inbox" folder.
        result, data = mail.uid('search', None, "UNSEEN")  # search and return

        if len(data) > 0 and data[0] != '':
            print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " There are " + str(len(data[0].split())) + " new messages."
            #print data[0].split()

            latest_email_uid = data[0].split()[-1]  # get the most recent e-mail id
            print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Downloading most recent e-mail..."
            result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')  # download the mos recent e-mail

            raw_email = data[0][1]
            email_message = email.message_from_string(raw_email)
            #print email_message['To']
            #print email_message['From']
            #print email_message['Subject']

            fromAddress = email_message['From']
            fromAddress = fromAddress[fromAddress.find('<')+1:fromAddress.find('>')]

            if fromAddress == 'some.address@email.com':
                # check if the e-mail has an attachment
                attachmentExists = False
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    attachmentExists = True
                    filename = part.get_filename()
                    if isTorrentFile(filename):
                        print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " The attached file is: " + filename
                        downloadLocation = settings.downloadPath

                        if not os.path.isfile(downloadLocation):
                            fileData = part.get_payload(decode=True)
                            if not fileData:
                                continue
                            fp = open(downloadLocation+filename, 'w')
                            fp.write(fileData)
                            fp.close()
                            sendSMTPMail(settings, 0, filename)
                    else:
                        print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Warning! : The attached file is not a torrent file."
                        sendSMTPMail(settings, 1, "The attached file is not a torrent file ("+filename+").")
                        continue

                if not attachmentExists:
                    print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Warning! : the e-mail message does not have an attachment."
                    sendSMTPMail(settings, 1, "The e-mail message does not have an attachment.")

                # delete the email when finished working with it
                print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Deleting message..."
                mail.uid("STORE",latest_email_uid,'+FLAGS', '(\Deleted)')
                mail.expunge()

            else:
                sendSMTPMail(settings, 1, "Received an e-mail from "+ fromAddress +".")

                print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Marking e-mail message as 'read'..."
                mail.uid("STORE", latest_email_uid, '+FLAGS', '(\Seen)')
                mail.expunge()

        else:
            print "{0} - No new messages. Exiting program.".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))

        mail.close()
        mail.logout()
        print datetime.now().strftime('%d-%m-%Y %H:%M:%S') + " Connection to " + settings.imapServer + " closed. Bye."

    # Catch server errors...
    except imaplib.IMAP4.abort as imaplibAbort:
        print "{0} - Server error ({1}): {2}".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), imaplibAbort.errno, imaplibAbort.strerror)
        mail.close()
        mail.logout()
        return -1
    # Catch other types of errors...
    except imaplib.IMAP4.error as imaplibError:
        print "{0} - IMAP error ({1}): {2}".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), imaplibError.errno, imaplibError.strerror)
        mail.close()
        mail.logout()
        return -1
    except SSLError:
        print "{0} - SSL error ({1}): {2}".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), SSLError.errno, SSLError.strerror)
        mail.close()
        mail.logout()
        return -1
    except socket.error:
        print "{0} - Socket error ({1}): {2}".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), socket.errno, socket.strerror)
        return -3

    return 0


def sendSMTPMail(settings, emailtype, text):
    """
    Type 0 means 'OK'
    Type 1 means 'Warning'
    Type -1 means 'Error'
    """
    
    # Create the root message and fill in the from, to, and subject headers
    msgRoot = email.MIMEMultipart.MIMEMultipart('related')
    msgRoot['Subject'] = 'Raspberry Pi Notification'
    msgRoot['From'] = settings.login
    msgRoot['To'] = settings.recipient
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = email.MIMEMultipart.MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    
    # We reference the image in the IMG SRC attribute by the ID we give it below
    #msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
    #msgAlternative.attach(msgText)
    
    if emailtype == 0:
        msgText = email.MIMEText.MIMEText('Received attachment ('+text+") downloaded succesfully at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        msgAlternative.attach(msgText)
        
        msgText = email.MIMEText.MIMEText('<table width=600><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Received attachment ('+text+") downloaded succesfully at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S')+"</td></tr></table>","html")
        msgAlternative.attach(msgText)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_ok.jpg', 'rb')
        msgImage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)
        
    elif emailtype == 1:
        msgText = email.MIMEText.MIMEText('Warning: '+text+" (at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S')+')')
        msgAlternative.attach(msgText)
        
        msgText = email.MIMEText.MIMEText('<table><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Warning: '+text+" (at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")</td></tr></table>","html")
        msgAlternative.attach(msgText)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_warn.jpg', 'rb')
        msgImage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)
        
    elif emailtype == -1:
        msgText = email.MIMEText.MIMEText('Error: '+text+" (at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")")
        msgAlternative.attach(msgText)
        
        msgText = email.MIMEText.MIMEText('<table width=600><tr><td align="center"><img src="cid:image1"/></td></tr><tr><td>Error: '+text+" (at "+datetime.now().strftime('%d-%m-%Y %H:%M:%S')+")</td></tr></table>","html")
        msgAlternative.attach(msgText)
        # This example assumes the image is in the current directory
        fp = open('/home/pi/Pictures/Status/raspi_error.jpg', 'rb')
        msgImage = email.MIMEImage.MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)

    # Send the email (this example assumes SMTP authentication is required)
    import smtplib
    smtp = smtplib.SMTP(settings.smtpServer, settings.smtpPort)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(settings.login.split('@')[0], settings.password)
    smtp.sendmail(settings.login, settings.recipient, msgRoot.as_string())
    smtp.quit()
