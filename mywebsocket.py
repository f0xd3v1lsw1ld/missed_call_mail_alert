#!#!/usr/bin/python
__author__ = 'f0xd3v1lsw1ld@gmail.com'
import socket
#from socket import EAGAIN
import struct
import hashlib
import base64
import signal
import sys
import time
import logging
import threading
import os

#setup logging
if 'logs' not in os.listdir("."):
    os.mkdir('logs')

logger = logging.getLogger('websocket')
logger.setLevel(logging.DEBUG)
#create console handler and set level to debug
#ch = logging.StreamHandler()
ch = logging.FileHandler("logs/webs.log")
ch.setLevel(logging.DEBUG)
#create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s:%(lineno)s - %(message)s')
#add FORMATTER to handler
ch.setFormatter(formatter)
# add console handler to logger
logger.addHandler(ch)


class WebSocketListener:
    def on_message(self, opcode, data, websocket):
        pass

    def on_connect(self, websocket):
        pass

    def on_close(self, websocket):
        pass

    def on_error(self, data, websocket):
        pass


class WebSocket:
    FRAME_BYTE1 = 0
    FRAME_BYTE2 = 1
    EXTENDED_PAYLOAD_LENGTH_16 = 2
    EXTENDED_PAYLOAD_LENGTH_64 = 3
    MASKING_KEY = 4
    PAYLOAD_DATA = 5
    #frame-opcode = frame-opcode-non-control /frame-opcode-control /frame-opcode-cont
    #frame-opcode-cont
    OC_FRAME_CONTINUATION = 0x00
    #frame-opcode-non-control
    OC_TEXT_FRAME = 0x01
    OC_BINARY_FRAME = 0x02
    #frame-opcode-control
    OC_CLOSE = 0x08
    OC_PING = 0x09
    OC_PONG = 0x0A

    def __init__(self, clientsocket, addr, _recv_hdlr):
        self.header_length = 2048
        # restrict the size of header and payload for security reasons
        self.maxheadersize = 0xffff
        self.maxpayload = 4194304
        self.handshaked = False
        self.client = clientsocket
        self.addr = addr
        self.alive = False
        self.client_id = clientsocket.fileno()
        self.recv_hdlr = _recv_hdlr

    def is_alive(self):
        if self.handshaked is True:
            self.alive = True
        return self.handshaked

    def handshake(self):
        self.handshaked = False
        header = {}
        logger.debug("client %d doing handshake", self.client_id)
        data = self.client.recv(self.header_length)
        if data:
            # accumulate multi packet transfer
            try:
                headerbuffer = str(data, 'utf-8')
            except:
                headerbuffer = str(data)
            if self.maxheadersize < len(headerbuffer):
                raise Exception(" header to large")

            #check end of HTTP header
            if headerbuffer.find("\r\n\r\n"):
                for line in headerbuffer.splitlines():
                    if ":" in line:
                        #print(line)
                        key, value = line.split(": ")
                        header[key] = value

                if 'Sec-WebSocket-Key' in header:
                    key = header['Sec-WebSocket-Key'].encode('utf-8')
                    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode('utf-8')
                    try:
                        response_str = str(base64.b64encode(hashlib.sha1(key + guid).digest()), encoding='utf8')
                    except:
                        response_str = str(base64.b64encode(hashlib.sha1(key + guid).digest()))
                    handshake_str = (
                                        "HTTP/1.1 101 Switching Protocols\r\n"
                                        "Upgrade: websocket\r\n"
                                        "Connection: Upgrade\r\n"
                                        "Sec-WebSocket-Accept: %s\r\n\r\n") % response_str
                    try:
                        self.client.send(bytes(handshake_str, 'UTF-8'))
                    except:
                        self.client.send(bytes(handshake_str))
                    logger.debug("client %d handshake done", self.client_id)
                    self.handshaked = True
                    self.recv_hdlr.on_connect(self)
                else:
                    raise Exception('Missing Sec-WebSocket-Key')

    def send(self, data):
        size = len(data)
        index = 0
        while size > 0:
            try:
                sent = self.client.send(data[index:size])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                index += sent
                size -= sent
            except socket.error as e:
                # if we have full buffers then wait for them to drain and try again
                if e.errno == socket.EAGAIN:
                    time.sleep(0.001)
                else:
                    raise e
            except Exception as n:
                logger.error("client %d "+str(n), self.client_id)
                self.handshaked = False
                return

    def send_msg(self, s):

        header = bytearray()
        is_string = isinstance(s, str)

        if is_string is True:
            header.append(0x81)
        else:
            header.append(0x82)

        b2 = 0
        length = len(s)

        if length <= 125:
            b2 |= length
            header.append(b2)
        #elif length >= 126 and length <= 65535:
        elif 126 <= length <= 65535:
            b2 |= 126
            header.append(b2)
            header.extend(struct.pack("!H", length))

        else:
            b2 |= 127
            header.append(b2)
            header.extend(struct.pack("!Q", length))

        self.send(header)

        if length > 0:
            if is_string is True:
                self.send(s.encode())
            else:
                self.send(s)

    def handle_app_data(self, data):
        logger.debug("client %d "+str(data, encoding='utf8'), self.client_id)
        test = "Hello"
        self.send_msg(test)

    def send_oc_control(self, opcode):
        frame_fin = 1
        frame_opcode = opcode
        frame_masked = 0
        frame_payload_length = 0
        msg = bytearray()

        msg.append((frame_fin << 7) | frame_opcode)
        msg.append((frame_masked << 7) | frame_payload_length)
        self.send(msg)

    def handle_opcode(self, opcode, data):
        if self.OC_CLOSE == opcode:
            try:
                self.send_oc_control(self.OC_CLOSE)
            except Exception as e:
                logger.error("OC_Close " + str(e))
            self.client.close()
            self.handshaked = False
            self.recv_hdlr.on_close(self)
        elif self.OC_PING == opcode:
            try:
                self.send_oc_control(self.OC_PING)
            except Exception as e:
                logger.error("OC_Ping " + str(e))
            logger.debug("client %d oc ping received", self.client_id)
        elif self.OC_PONG == opcode:
            try:
                self.send_oc_control(self.OC_PONG)
            except Exception as e:
                logger.error("OC_Pong " + str(e))
            logger.debug("client %d oc pong received", self.client_id)
        elif self.OC_FRAME_CONTINUATION == opcode or self.OC_TEXT_FRAME == opcode or self.OC_BINARY_FRAME == opcode:
            #try:
                self.recv_hdlr.on_message(opcode, data, self)
           # except Exception as e:
            #    logger.error("OC_Data opcode(" + str(opcode) + ") " + str(e) + data.decode("uft-8"))

    def parseframe(self, data):
        #for python 2.7 because socket.recv returns str not byte object like in python 3
        if isinstance(data, str):
            _data = bytearray(data)
        else:
            _data = data
        state = self.FRAME_BYTE1
        fin = -1
        opcode = -1
        mask = bytearray()
        masked = False
        payload_length = 0
        extended_payload_length = bytearray()
        app_data = bytearray()
        index = 0
        for onebyte in _data:
            myascii = onebyte
            if state == self.FRAME_BYTE1:
                fin = (myascii & 0x80)
                opcode = (myascii & 0x0F)
                #todo handle rsv1-3
                state = self.FRAME_BYTE2
            elif state == self.FRAME_BYTE2:
                mask_bit = (myascii & 0x80) >> 7
                payload_length = (myascii & 0x7F)
                #todo check this hack for disconation
                if payload_length <= 0:
                    self.handle_opcode(opcode, None)
                if 1 == mask_bit:
                    masked = True
                if payload_length <= 125:
                    if masked is True:
                        state = self.MASKING_KEY
                    else:
                        if payload_length <= 0:
                            self.handle_opcode(opcode, None)
                        else:
                            #todo add error handling, data recieved from client must be masked
                            pass
                elif payload_length == 126:
                    state = self.EXTENDED_PAYLOAD_LENGTH_16
                elif payload_length == 127:
                    state = self.EXTENDED_PAYLOAD_LENGTH_64
            elif state == self.EXTENDED_PAYLOAD_LENGTH_16:

                extended_payload_length.append(myascii)

                if len(extended_payload_length) > 2:
                    raise Exception("WS_EXTENDED_PAYLOAD_LENGTH_16 to large")
                elif len(extended_payload_length) == 2:
                    payload_length = struct.unpack_from('!H', str(extended_payload_length))[0]

                if masked is True:
                    state = self.MASKING_KEY
                else:
                    #todo add error handling, data recieved from client must be masked
                    pass

            elif state == self.EXTENDED_PAYLOAD_LENGTH_64:
                extended_payload_length.append(myascii)
                if len(extended_payload_length) > 8:
                    raise Exception("WS_EXTENDED_PAYLOAD_LENGTH_64 to large")
                elif len(extended_payload_length) == 8:
                    payload_length = struct.unpack_from('!Q', str(extended_payload_length))[0]
                if masked is True:
                    state = self.MASKING_KEY
                else:
                    #todo add error handling, data recieved from client must be masked
                    pass
            elif state == self.MASKING_KEY:
                mask.append(myascii)
                if len(mask) > 4:
                    raise Exception("WS_MASKING_KEY to large")
                elif len(mask) == 4:
                    state = self.PAYLOAD_DATA
            elif state == self.PAYLOAD_DATA:
                if masked is True:
                    app_data.append(myascii ^ mask[index % 4])
                else:
                    app_data.append(myascii)
                if len(app_data) >= self.maxpayload:
                    raise Exception("WS_PAYLOAD_DATA size to large")
                if (index + 1) == payload_length:
                    self.handle_opcode(opcode, app_data)
                    return
                else:
                    index += 1
            else:
                raise Exception("Error during WS frame parsing")

    def handledata(self):
        self.handshake()
        if self.handshaked is True:
            while self.handshaked is True:
                try:
                    data = self.client.recv(2048)
                    if data:
                        try:
                            self.parseframe(data)
                        except Exception as n:
                            logger.error("client %d " + str(n) + data.decode("utf-8", 'ignore'),self.client_id)
                            self.send_oc_control(self.OC_CLOSE)
                            self.client.close()
                            self.handshaked = False
                            return

                except Exception as n:
                    logger.error("client %d" + str(n)+" 277", self.client_id)
                    self.client.close()
                    self.handshaked = False
                    return

        else:
            logger.debug("handshake failed")
            self.handshaked = False


class WebSocketThread(threading.Thread):
    def __init__(self, clientsocket, addr, _recv_hdlr):
        super(WebSocketThread, self).__init__()
        self.client = clientsocket
        self.addr = addr
        self.running = False
        self.client_id = clientsocket.fileno()
        self.recv_hdlr = _recv_hdlr
        self.websocket = WebSocket(self.client, self.addr, self.recv_hdlr)


    def run(self):
        self.running = True
        #logger.debug("server connected to", self.addr[0])
        while self.running:
            self.websocket.handledata()
            if self.websocket.is_alive() is False:
                self.stop()

    def stop(self):
        self.running = False
        self.client.close()
        logger.debug("thread "+str(self.client_id)+" stopped")


class Server:
    def __init__(self, port, _receiver):
        self.port = port
        self.running = False
        self.thread_list = {}
        self.receiver = _receiver
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        self.sock.listen(1)

    def stop(self):
        self.running = False
        for thread in self.thread_list:
            try:
                thread.stop()
            except Exception as e:
                logger.error(str(e))

        self.sock.close()
        logger.debug("server stopped")

    def start(self):
        self.running = True
        logger.debug("server started on %s[%s] and listen on port: %s", socket.gethostname(), socket.gethostbyname(socket.gethostname()), self.port)
        while self.running:
            clientsocket, addr = self.sock.accept()
            fileno = clientsocket.fileno()
            thread = WebSocketThread(clientsocket, addr, self.receiver)
            thread.start()
            self.thread_list[fileno] = thread


class ExcampleHandler(WebSocketListener):
    def __init__(self):
        pass

    def on_message(self, opcode, data, websocket):
        if opcode is websocket.OC_FRAME_CONTINUATION:
            logger.debug("handler: OC_FRAME_CONTINUATION: %s", data)
        elif opcode is websocket.OC_BINARY_FRAME:
            logger.debug("handler: OC_BINARY_FRAME: %s", data)
        elif opcode is websocket.OC_TEXT_FRAME:
            logger.debug("handler: OC_TEXT_FRAME: %s", data.decode("utf-8"))

        websocket.send_msg("Hello again")

    def on_connect(self, websocket):
        logger.debug("handler: Client connected")
        websocket.send_msg("You'r welcome")

    def on_close(self, websocket):
        logger.debug("handler: Connection closed")

    def on_error(self, data, websocket):
        logger.error("handler: Error in websocket connction")

if __name__ == "__main__":
    handler = ExcampleHandler()
    ws_server = Server(8001, handler)

    def close_sig_handler(s, frame):
        if s == signal.SIGINT:
            ws_server.stop()
            sys.exit(0)

    signal.signal(signal.SIGINT, close_sig_handler)
    ws_server.start()
