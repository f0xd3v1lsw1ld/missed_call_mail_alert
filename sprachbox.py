__author__ = 'f0xd3v1lsw1ld@gmail.com'
import imaplib
import email
import datetime
import os
import time
import logging

logger = logging.getLogger('email_notification')


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class CVoiceMail(object):
    def __init__(self, _from, _date, _subject, _attachment):
        self.msender = _from
        self.mdate = _date
        self.msubject = _subject
        self.mattachment = _attachment
        self.logger = logging.getLogger('email_notification.CVoiceMail')
        self.logger.debug("%s %s %s %s", self.msender, self.mdate, self.msubject, self.mattachment)

    def number(self):
        return self.msender[0]

    def date(self):
        return self.mdate

    def subject(self):
        return self.msubject

    def attachment(self):
        return self.mattachment


class Csprachbox(object):
    def __init__(self, imap_server, mailbox, user, password):
        self.attach_dir = '.'
        if 'attachments' not in os.listdir(self.attach_dir):
            os.mkdir('attachments')
        self.imap_server = imap_server
        self.user = user
        self.password = password
        self.mailbox = mailbox
        self.logger = logging.getLogger('email_notification.Csprachbox')

        self.mails = []

    def print_error(self, messages):
        for message in messages:
            self.logger.error(message.decode("utf-8"))

    def store_attachment(self, msg):
        filepath = ""
        for part in msg.walk():
            try:
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()

                if bool(filename):
                    filepath = os.path.join(self.attach_dir, 'attachments', filename)
                    if not os.path.isfile(filepath):
                        self.logger.info("download new attachment %s", filename)
                    fp = open(filepath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

            except Exception as e:
                self.logger.error(str(e))

        return filepath

    def download_attachments(self):
        try:
            im = imaplib.IMAP4_SSL(self.imap_server)

            typ, accountdetails = im.login(self.user, self.password)
            if typ == "NO":
                self.print_error(accountdetails)
                raise MyError(("Failed to login to %s with user %s", self.imap_server, self.user))
            self.logger.debug("login to \"%s\"", self.imap_server)

            status, messages = im.select(self.mailbox, readonly=True)
            if status == "NO":
                self.print_error(messages)
                raise MyError(("Failed to select mailbox %s", self.mailbox))
            self.logger.debug("\"%s\" selected", self.mailbox)

            #search for all emails from yesterday till now
            yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, messages = im.search(None, '(SINCE {0})'.format(yesterday))
            self.logger.info("%s voicemail(s) since %s", len(messages[0].split()), yesterday)

            #loop over all messages
            for mailnr in messages[0].split():
                status, messages = im.fetch(mailnr, '(RFC822)')
                if status == "NO":
                    self.print_error(messages)
                    raise MyError(("Failed to fetch mail Nr. %s", str(mailnr)))

                    #parse message as email object
                msg = email.message_from_string(messages[0][1].decode("utf-8"))

                try:
                    # only for python 3
                    #self.mails.append(CMail(email.utils.parseaddr(msg['From']),
                    #                        email.utils.parsedate_to_datetime(msg.get('date')).strftime("%d.%m.%Y"),
                    #                        msg.get('subject'),
                    #                        self.store_attachment(msg)))

                    #workaround for python 2.7
                    self.mails.append(CVoiceMail(email.utils.parseaddr(msg['From']),
                                                 time.strftime("%d.%m.%Y", email.utils.parsedate(msg.get('date'))),
                                                 msg.get('subject'),
                                                 self.store_attachment(msg)))
                except Exception as e:
                    self.logger.error(str(e))
                    pass
            im.close()
            im.logout()

        except Exception as e:
            self.logger.error(str(e))

    def find_voice_mail_from(self, number, date):
        self.logger.debug("number: %s date: %s", number, date)
        attachment = ""
        for mail in self.mails:
            self.logger.debug("%s %s %s", mail.number(), mail.date(), mail.subject())
            #[BUGFIX] 2015.03.20 Wenn in der telekom sprachbox Email die Nummer mit 49 beginnt muss diese durch 0\
            #ersetzt werden. Ansonsten wird die Nummer nicht gefunden und der Anhang wird nicht an die EMail angehangen.
            voicemail_number = mail.number()

            if voicemail_number.startswith("49"):
                voicemail_number = "0"+voicemail_number[2:]

            if number == voicemail_number:
                self.logger.debug("number found: %s", number)
                if date == mail.date():
                    self.logger.debug("date found: %s", date)
                    if mail.subject().startswith("Sprachnachricht"):
                        self.logger.debug("message with attachment found: %s", mail.subject())
                        attachment = mail.attachment()
        return attachment
