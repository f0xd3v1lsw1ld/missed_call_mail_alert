#!/usr/bin/python
__author__ = 'f0xd3v1lsw1ld@gmail.com'
import sqlite3
import logging
import json
import mywebsocket
import signal
import threading
import sys
import time
import os
try:
    import thread
except ImportError:
    import _thread as thread


def _seconds_to_timestring(secs):
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def convert_time(timestr):
    septime = timestr.split(':')
    return int(septime[2]) + 60*int(septime[1]) + 60*60*int(septime[0])


def jdefault(o):
    return o.__dict__


class Ccaller(object):
    def __init__(self, caller_number):
        self.number = caller_number
        self.number_of_calls = 0
        self.missed_calls = 0
        self.duration = 0
        self.name = ""

    def get_n(self):
        return self.number

    def set_noc(self, count):
        self.number_of_calls = count

    def get_noc(self):
        return self.number_of_calls

    def add_noc(self):
        self.number_of_calls += 1

    def set_mc(self, count):
        self.missed_calls = count

    def get_mc(self):
        return self.missed_calls

    def add_mc(self):
        self.missed_calls += 1

    def set_d(self, duration):
        self.duration = duration

    def get_d(self):
        return self.duration

    def add_d(self, secs):
        self.duration += secs

    def set_name(self, _name):
        self.name = _name

    def get_name(self):
        return self.name


class Analyse(mywebsocket.WebSocketListener):

    sql_insert_contact = "INSERT OR REPLACE INTO contacts VALUES (?,?)"
    lock = thread.allocate_lock()

    def __init__(self):
        #setup logging
        if 'logs' not in os.listdir("."):
            os.mkdir('logs')
        self.logger = logging.getLogger('analyse')
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        self.ch = logging.FileHandler("logs/webs.log")
        #self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        #create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s:%(lineno)s - %(message)s')
        #add FORMATTER to handler
        self.ch.setFormatter(formatter)
        # add console handler to logger
        self.logger.addHandler(self.ch)
        #create dict
        self.dictionary = {}
        self.jstr = ""

    def start(self):

        self.logger.debug("start")

        self.lock.acquire()
        connection = sqlite3.connect("calllist.db")
        cursor = connection.cursor()
        #find all numbers

        cursor.execute("SELECT number FROM calllist")

        for number in cursor:
            self.dictionary[number[0]] = Ccaller(number[0])
        self.lock.release()
        for key in self.dictionary.keys():
            self.dictionary[key].set_name(self.find_name(key))
        t1 = time.clock()
        for key in sorted(self.dictionary.keys()):
            #logger.debug(dictionary[key])
            cursor.execute("SELECT * FROM calllist WHERE number = ?", (key,))
            self.dictionary[key].set_noc(0)
            self.dictionary[key].set_mc(0)
            for entry in cursor:

                seconds = entry[3]
                self.dictionary[key].add_d(seconds)
                self.dictionary[key].add_noc()
                if seconds == 0:
                    self.dictionary[key].add_mc()
            #divider = abs(self.dictionary[key].get_noc() - self.dictionary[key].get_mc())
            #if divider == 0:
            #    divider = 1
            #self.logger.debug("statistic of %s: calls %s (missed %s) duration %s mean value %s",
            #             key, self.dictionary[key].get_noc(), self.dictionary[key].get_mc(),
            #             _seconds_to_timestring(self.dictionary[key].get_d()),
            #             _seconds_to_timestring(self.dictionary[key].get_d()/divider))
        t2 = time.clock()
        self.jstr = json.dumps(self.dictionary, default=jdefault, indent=4)
           # self.logger.debug(jstr)
        #with open("statistic.json", 'w') as outfile:
        #       json.dump(self.dictionary, outfile, default=jdefault)

        dt = t2 - t1
        self.logger.debug("Rechenzeit: "+str(dt))

    def on_message(self, opcode, data, websocket):
        #self.start()
        if opcode is websocket.OC_FRAME_CONTINUATION:
            self.logger.debug("handler: OC_FRAME_CONTINUATION: %s", data)
        elif opcode is websocket.OC_BINARY_FRAME:
            self.logger.debug("handler: OC_BINARY_FRAME: %s", data)
        elif opcode is websocket.OC_TEXT_FRAME:
            #self.logger.debug("handler: OC_TEXT_FRAME: %s", data.decode("utf-8"))
            #self.logger.debug(data)
            try:
                #self.logger.debug(json.loads(data.decode("utf-8",'ignore')))
                data = json.loads(data.decode("utf-8"))
            except Exception as e:
                self.logger.error(str(e))
                return

            if "modify" in data:
                if "name" in data["modify"] and "number" in data["modify"]:
                    #self.logger.debug(data["modify"]["number"]+": "+data["modify"]["name"])
                    #try:
                    number = str(data["modify"]["number"])
                    name = str(data["modify"]["name"])
                    if type(number) is str and type(name) is str:
                        d = threading.Thread(name='daemon', target=self.update_name_in_db, args=(number, name,))
                        d.setDaemon(True)
                        d.start()
                        #self.update_name_in_db(number, name)
                    #self.update_name_in_db(data["modify"]["number"], data["modify"]["name"])
                    #except Exception as e:
                     #   self.logger.error(e)

    def on_connect(self, websocket):
        self.logger.debug("handler: Client connected")
        self.start()
        #websocket.send_msg('['+self.jstr+']')
        websocket.send_msg(self.jstr)

    def on_close(self, websocket):
        self.logger.debug("handler: Connection closed")

    def on_error(self, data, websocket):
        self.logger.error("handler: Error in websocket connction")

    def find_name(self, number):
        self.lock.acquire()
        connection = sqlite3.connect("calllist.db")
        subject = ""
        cur = connection.cursor()
        cur.execute("SELECT Name FROM contacts WHERE number = ?", (str(number),))
        for name in cur:
            subject += name[0]
        self.lock.release()
        if subject is "":
            subject = "unknown"

        return subject

    def update_name_in_db(self, number, name):
        if type(number) is not str or type(name) is not str:
            self.logger.error("Contact isn't a str.")
            return
        if type(number) is None or type(name) is None:
            self.logger.error("Number or name is none.")
            return

        self.logger.debug(str(number) + ": " + str(name))
        try:
            self.lock.acquire()
            con = sqlite3.connect("calllist.db")
            cur = con.cursor()
            contact = (number, name)
            cur.execute(self.sql_insert_contact, contact)
            con.commit()
            self.lock.release()
        except Exception as e:
            self.logger.error(e)


if __name__ == "__main__":
    analyse = Analyse()
    analyse.start()
    ws_server = mywebsocket.Server(8001, analyse)

    def close_sig_handler(s, frame):
        if s == signal.SIGINT:
            ws_server.stop()
            sys.exit(0)

    signal.signal(signal.SIGINT, close_sig_handler)
    ws_server.start()
