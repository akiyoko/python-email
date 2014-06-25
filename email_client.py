# -*- coding: utf-8 -*-
import re
import time
from getpass import getpass

import email
from email.header import decode_header
from email.Header import Header
from email.MIMEText import MIMEText
from email import Utils
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

    def send_email(self, from_address, to_addresses, cc_addresses, bcc_addresses, subject, body):
        """
        Send an email

        Args:
            to_addresses: must be a list
            cc_addresses: must be a list
            bcc_addresses: must be a list
        """
        try:
            # Note: need Python 2.6.3 or more
            conn = SMTP_SSL(self.smtp_host, self.smtp_port)
            conn.login(self.user, self.password)
            msg = MIMEText(body, 'plain', self.email_default_encoding)
            msg['Subject'] = Header(subject, self.email_default_encoding)
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)
            if cc_addresses:
                msg['CC'] = ', '.join(cc_addresses)
            if bcc_addresses:
                msg['BCC'] = ', '.join(bcc_addresses)
            msg['Date'] = Utils.formatdate(localtime=True)
            # TODO: Attached file
            conn.sendmail(from_address, to_addresses, msg.as_string())
        except:
            raise
        finally:
            conn.close()

    def get_email(self, from_address, subject_pattern=None):
        """
        Get the latest unread email
        """
        timeout = time.time() + self.timeout
        try:
            conn = IMAP4_SSL(self.imap_host, self.imap_port)
            while True:
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
                    if subject_pattern and re.match(subject_pattern, msg_subject.decode(msg_encoding)) is None:
                        continue
                    # TODO: Cannot use when maintype is 'multipart'
                    return {
                        'from_address': msg.get('From'),
                        'to_addresses': msg.get('To'),
                        'cc_addresses': msg.get('CC'),
                        'bcc_addresses': msg.get('BCC'),
                        'date': msg.get('Date'),
                        'subject': msg_subject.decode(msg_encoding),
                        'body': msg.get_payload().decode(msg_encoding),
                        # TODO: Attached file
                    }
                if time.time() > timeout:
                    raise Exception("Timeout!")
                time.sleep(5)
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
    email_client.send_email(email_address, [email_address], None, None, u"テスト", u"テストメールです")

    # Check the email
    email = email_client.get_email(email_address, u"テスト")
    print "from_address=%s" % email['from_address']
    print "to_addresses=%s" % email['to_addresses']
    print "cc_addresses=%s" % email['cc_addresses']
    print "bcc_addresses=%s" % email['bcc_addresses']
    print "date=%s" % email['date']
    print "subject=%s" % email['subject']
    print "body=%s" % email['body']
