#!/usr/bin/python
__author__ = 'f0xd3v1lsw1ld@gmail.com'

from mail import build_msg
import sqlite3
import csv
import logging
import os
import datetime
import mail
import sprachbox
import ConfigParser


#setup logging
if 'logs' not in os.listdir("."):
    os.mkdir('logs')
today = (datetime.date.today()).strftime("%Y-%m-%d")
logfile = "logs/"+today+".log"

# logger = logging.getLogger('email_notification')create logger
logger = logging.getLogger('email_notification')
logger.setLevel(logging.DEBUG)
#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(logfile)
fh.setLevel(logging.DEBUG)
#create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s: %(message)s')
#add FORMATTER to handler
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add console handler to logger
logger.addHandler(ch)
logger.addHandler(fh)

logger.debug("start")

def convert_duration_to_sec(duration):
    hh,mm,ss = duration.split(':')
    seconds = int(ss) + int(mm)*60 + int(hh)*60*60
    return seconds

def main():
    _sections = ['input', 'sprachbox', 'mail', 'notification']
    _in_options = ['db_filename', 'calllist', 'contacts', 'db_schema']
    _sb_options = ['imap_server', 'imap_mailbox', 'imap_username', 'imap_password']
    _mail_options = ['smtp_server', 'smtp_user', 'smtp_password', 'smtp_fromaddr']
    _note_options = ['to']
    _config = ConfigParser.ConfigParser()

    hdl_contacts = True
    sbox = None
    cmail = None

    try:
        _config.read("mailbox.ini")
    except Exception as e:
        logger.fatal(e)
        return
    #Validation of Section INPUT
    if _config.has_section(_sections[0]):
        for option in _in_options:
            if not _config.has_option(_sections[0], option):
                if option is not _in_options[2]:
                    logger.fatal("Missing option %s in Section: %s" % (option, _sections[0]))
                    return
                else:
                    logger.warning("Missing option %s in Section: %s" % (option, _sections[0]))
                    logger.warning("Assignment of Number to Name disabled")
                    hdl_contacts = False
    else:
        logger.fatal("Missing init Section: %s" % _sections[0])
    #Validation of Section Sprachbox
    if _config.has_section(_sections[1]):
        for option in _sb_options:
            if not _config.has_option(_sections[1], option):
                logger.fatal("Missing option %s in Section: %s" % (option, _sections[1]))
                return
        hdl_sprachbox = True
    else:
        logger.warning("Missing init Section: %s" % _sections[1])
        logger.warning("Download Voicemails from Sprachbox disabled")
        hdl_sprachbox = False

    #Validation of Section Mail
    if _config.has_section(_sections[2]):
        for option in _mail_options:
            if not _config.has_option(_sections[2], option):
                logger.fatal("Missing option %s in Section: %s" % (option, _sections[1]))
                return
        hdl_mail = True
    else:
        logger.warning("Missing init Section: %s" % _sections[2])
        logger.warning("Sent E-Mail for missed calls disabled")
        hdl_mail = False

    #Validation of Section Notification
    if _config.has_section(_sections[3]):
        if _config.has_option(_sections[3], _note_options[0]):
            send_to = _config.get(_sections[3], _note_options[0]).replace(' ', '').split(',')
        else:
            logger.warning("Missing option %s in Section: %s" % (_note_options[0], _sections[3]))
            logger.warning("Send E-Mail for missed calls to default address %s" % _config.get(_sections[2],
                                                                                              _mail_options[1]))
            send_to = _config.get(_sections[2], _mail_options[1])
    else:
        logger.warning("Missing init Section: %s" % _sections[3])
        logger.warning("Send E-Mail for missed calls to default address %s" % _config.get(_sections[2],
                                                                                          _mail_options[1]))
        send_to = _config.get(_sections[2], _mail_options[1])

    # init to imap mailbox of telekom sprachbox
    if hdl_sprachbox is True:
        sbox = sprachbox.Csprachbox(_config.get(_sections[1], _sb_options[0]),
                                    _config.get(_sections[1], _sb_options[1]),
                                    _config.get(_sections[1], _sb_options[2]),
                                    _config.get(_sections[1], _sb_options[3]))
        sbox.download_attachments()

    #init connection to smtp mail konto
    if hdl_mail is True:
        cmail = mail.CsmtpMail(_config.get(_sections[2], _mail_options[0]),
                               _config.get(_sections[2], _mail_options[1]),
                               _config.get(_sections[2], _mail_options[2]),
                               _config.get(_sections[2], _mail_options[3]))
        #use this to disable the e-mail send process, a dummy will be print with the logger
        if _config.has_option(_sections[2], "smtp_debug"):
            cmail.set_debug(True)

    # create database as file
    db_is_new = not os.path.exists(_config.get(_sections[0], _in_options[0]))
    db_schema = _config.get(_sections[0], _in_options[3])
    with sqlite3.connect(_config.get(_sections[0], _in_options[0])) as connection:
            if db_is_new:
                logger.debug('Creating database schema from file %s',db_schema)
                with open(db_schema, 'rt') as file:
                    schema = file.read()
                connection.executescript(schema)
            else:
                logger.debug('Database exists, assume schema does, too.')




    sql_insert_call = "INSERT OR IGNORE INTO calllist VALUES (?,?,?,?,?)"

    sql_insert_contact = "INSERT OR IGNORE INTO contacts VALUES (?,?)"

    try:
        with sqlite3.connect(_config.get(_sections[0], _in_options[0])) as connection:
            cursor = connection.cursor()
            fobj = open(_config.get(_sections[0], _in_options[1]), "r")
            for line in fobj:
                if len(line) > 0:
                    call_list = line.split("new Array")
                    for item in call_list:
                        details = item.replace('\n', '').replace('\r', '').split(',')
                        if len(details) > 3:
                            #_datetime = details[0].split(" ")
                            #value = (_datetime[0], _datetime[1], details[1], details[2], details[3], "False")
                            _datetime = datetime.datetime.strptime(details[0],"%d.%m.%Y %H:%M:%S" )
                            number = details[1]
                            port = details[2]
                            duration = convert_duration_to_sec(details[3])
                            value = (_datetime, number, port, duration, 0)
                            logger.debug("new call %s", str(value))
                            cursor.execute(sql_insert_call, value)
            connection.commit()
            fobj.close()
    except Exception as e:
        logger.error(str(e))


    if hdl_contacts is True:
        try:
            with sqlite3.connect(_config.get(_sections[0], _in_options[0])) as connection:
                cursor = connection.cursor()
                reader = csv.DictReader(open(_config.get(_sections[0], _in_options[2]), "r"), delimiter=",")
                for line in reader:
                    contact = (line["Nummer"], line["Name"])
                    cursor.execute(sql_insert_contact, contact)
                connection.commit()
        except Exception as e:
            logger.error(str(e))

    with sqlite3.connect(_config.get(_sections[0], _in_options[0])) as connection:
        cursor = connection.cursor()

        #find missed calls
        cursor.execute("SELECT * FROM calllist WHERE duration = 0 AND notification = 0")
        cur = connection.cursor()
        for row in cursor:
            debugstr = ""

            for tup in row:
                if isinstance(tup, str):
                    debugstr += tup
                elif isinstance(tup,int):
                    debugstr += str(tup)
                else:
                    debugstr += tup.decode("utf-8")
                debugstr += " "

            logger.debug("handle call: %s", debugstr)
            subject = 'Anruf von '
            date_time = str(row[0])
            number = str(row[1])
            if number == ' ':
                subject += 'unbekannt'
                #english for email from sprachbox
                number = "unknown"
            else:
                cur.execute("SELECT Name FROM contacts WHERE number = ?", (number,))
                name_found = False
                for name in cur:
                    subject += name[0]+" ("+number+")"
                    name_found = True
                if name_found is False:
                    subject += number
                #number = str(row[2])

            if hdl_sprachbox is True and sbox is not None:
                attachment = sbox.find_voice_mail_from(number, date_time)
                if hdl_mail is True and cmail is not None:
                    if attachment != "":
                        for address in send_to:
                            cmail.sendmail_attachment(address, subject, build_msg(row), attachment)
                    else:
                        for address in send_to:
                            cmail.sendmail(address, subject, build_msg(row))
                        continue

        #Replace calls who we send a notification
        cursor.execute("UPDATE calllist SET notification = 1 WHERE duration = 0 AND notification = 0")
        connection.commit()


if __name__ == "__main__":
    main()
