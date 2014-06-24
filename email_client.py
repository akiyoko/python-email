# -*- coding: utf-8 -*-
import time
from getpass import getpass

from email.header import decode_header
from email.Header import Header
from email.MIMEText import MIMEText
import email.Utils
from imaplib import IMAP4_SSL
from smtplib import SMTP_SSL


LOGIN_USERNAME = None
LOGIN_PASSWORD = None


class EmailClient(object):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 465
        self.imap_host = 'imap.gmail.com'
        self.imap_port = 993
        self.email_default_encoding = 'iso-2022-jp'
        self.timeout = 1 * 60  # sec

    def send_email(self, from_address, to_address, subject, body):
        """
        Send an email
        """
        if not isinstance(to_address, list):
            raise Exception("to_address must be a list.")
        try:
            # Note: over Python 2.6.3
            conn = SMTP_SSL(self.smtp_host, self.smtp_port)
            conn.login(self.user, self.password)
            msg = MIMEText(body, 'plain', self.email_default_encoding)
            msg['Subject'] = Header(subject, self.email_default_encoding)
            msg['From'] = from_address
            msg['To'] = ', '.join(to_address)
            # TODO: CC, BCC, Attached file
            msg['Date'] = email.Utils.formatdate(localtime=True)
            conn.sendmail(from_address, to_address, msg.as_string())
        except:
            raise
        finally:
            conn.close()

    def get_email(self, from_address, subject=None):
        """
        Get the latest unread email
        """
        timeout = time.time() + self.timeout
        try:
            conn = IMAP4_SSL(self.imap_host, self.imap_port)
            while True:
                time.sleep(5)
                # Note: If you want to search unread emails, you should login after new emails are arrived
                conn.login(self.user, self.password)
                conn.list()
                conn.select('inbox')
                #typ, data = conn.search(None, 'ALL')
                #typ, data = conn.search(None, '(UNSEEN HEADER Subject "%s")' % subject)
                #typ, data = conn.search(None, '(ALL HEADER FROM "%s")' % from_address)
                # Search unread ones
                typ, data = conn.search(None, '(UNSEEN HEADER FROM "%s")' % from_address)
                ids = data[0].split()
                print "ids=%s" % ids
                # Search from backwards
                for id in ids[::-1]:
                    typ, data = conn.fetch(id, '(RFC822)')
                    raw_email = data[0][1]
                    msg = email.message_from_string(raw_email)
                    msg_subject = decode_header(msg.get('Subject'))[0][0]
                    msg_encoding = decode_header(msg.get('Subject'))[0][1] or self.email_default_encoding
                    if subject and subject != msg_subject.decode(msg_encoding):
                        continue
                    # TODO: Cannot use when maintype is 'multipart'
                    return {
                        'subject': msg_subject.decode(msg_encoding),
                        'body': msg.get_payload().decode(msg_encoding),
                    }
                if time.time() > timeout:
                    raise Exception("Timeout!")
        except:
            raise
        finally:
            conn.close()
            conn.logout()


if __name__ == "__main__":
    email_address = raw_input("Enter email address: ") if not LOGIN_USERNAME else LOGIN_USERNAME
    email_password = getpass("Enter email password: ") if not LOGIN_PASSWORD else LOGIN_PASSWORD

    email_client = EmailClient(email_address, email_password)
    # Send an email to myself
    email_client.send_email(email_address, [email_address], u"テスト", u"テストメールです")

    # Check the email
    email = email_client.get_email(email_address)
    print "subject=%s" % email['subject']
    print "body=%s" % email['body']
