__author__ = 'f0xd3v1lsw1ld@gmail.com'


class Ccall(object):
    def __init__(self, date, time, number, port, duration, notification):
        self.date = date
        self.time = time
        if number is " ":
            self.number = "unknown"
        else:
            self.number = number
        self.port = port
        self.duration = duration
        self.notification = notification
        return

    def __del__(self):
        return

    def print_call(self):
        print('  ' + self.time + ',' + self.number + ',' + self.port + ',' + self.duration + ',' + self.notification)

    def get_all(self):
        __strg = "<p><b>Time: </b>" + self.time + "</p>"
        __strg += "<p><b>Phone number: </b>" + self.number + "</p>"
        __strg += "<p><b>Speedport Port: </b>" + self.port + "</p>"
        __strg += "<p><b>Speech duration: </b>" + self.duration + "</p>"
        return __strg

    def get_datetime(self):
        return self.date + " " + self.time
