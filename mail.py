__author__ = 'f0xd3v1lsw1ld@gmail.com'
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
import logging
import smtplib

logger = logging.getLogger('email_notification')
maillogger = logging.getLogger('email_notification.mail')


def build_msg(tup):
    if len(tup) != 5:
        return
    try:
        date_time = tup[0].split(" ")
        reti = "Datum: " + date_time[0] + "\n\r"
        reti += "Uhrzeit: " + date_time[1] + "\n\r"
        return reti
    except Exception as e:
        self.logger.error(str(e))
        return


class CsmtpMail(object):
        def __init__(self, _smtp_server, _user, _passw, _fromaddr):
            self.smtp_server = _smtp_server
            self.user = _user
            self.password = _passw
            self.fromaddr = _fromaddr
            self.logger = logging.getLogger('email_notification.CsmtpMail')
            self.debug = False

        def set_debug(self, mode):
            self.debug = mode
            if self.debug:
                self.logger.info("enable debug mode")
            else:
                self.logger.info("disable debug mode")

        @staticmethod
        def create(from_addr, to_addr, subject, message):
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(message))
            return msg

        def send(self, to_addr, msg):
            # Sending the mail
            try:
                server = smtplib.SMTP(self.smtp_server)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.user, self.password)
                server.sendmail(self.user, to_addr, msg.as_string())
                server.quit()
            except Exception as e:
                self.logger.error(str(e))

        def sendmail(self, receiver, subject, message):
            if not receiver:
                return
            if not subject:
                return
            if self.debug is False:
                self.send(receiver, self.create(self.user, receiver, subject, message))
                self.logger.debug("send mail from %s to %s with subject %s", self.fromaddr, receiver, subject)
            else:
                self.logger.debug("dummy send mail from %s to %s with subject %s", self.fromaddr, receiver, subject)

        def sendmail_attachment(self, receiver, subject, message, filename):
            if not receiver:
                return
            if not subject:
                return
            # Writing the message (this message will appear in the email)
            msg = self.create(self.user, receiver, subject, message)
            try:
                mp3 = MIMEAudio(open(filename, "rb").read(), "mpeg")

                mp3.add_header('Content-Disposition', 'attachment', filename="voice_message.mp3")
                msg.attach(mp3)
            except Exception as e:
                self.logger.ERROR(str(e))
                pass
            if self.debug is False:
                self.send(receiver, msg)
                self.logger.debug("send mail from %s to %s with subject %s and attachment %s",
                                  self.fromaddr, receiver, subject, filename)
            else:
                self.logger.debug("dummy send mail from %s to %s with subject %s and attachment %s",
                                  self.fromaddr, receiver, subject, filename)
