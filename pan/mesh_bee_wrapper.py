#   Wrapper for Mesh Bee library
#   helping to easier communicate with Mesh Bee module
#
#   Copyright (C) 2014 at seeedstudio
#   Author: Jack Shao (jacky.shaoxg@gmail.com)
#
#   The MIT License (MIT)
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#   THE SOFTWARE.



import os
import re
import glob
import binascii
import logging
from pan.mesh_bee import *
from factory import Factory

class MeshBeeWrapper(object):
    """
    """
    default_port_name = 'serial'

    serial = None
    meshbee = None
    logger = None

    buffer = dict()

    def log(self, level, message):
        if self.logger:
            self.logger.log(level, message)

    def disconnect(self):
        """
        Closes serial port
        """
        self.meshbee.halt()
        self.serial.close()
        return True

    def connect(self):
        """
        Creates an meshbee instance
        """
        try:
            self.log(logging.INFO, "Connecting to meshbee")
            self.meshbee = MeshBee(self.serial, self.logger, callback=self.process)
        except Exception,e:
            print e
            return False
        return True

    def process(self, packet):

        self.log(logging.DEBUG, packet)

        try:
            address = packet['src_addr64']
        except KeyError:
            self.log(logging.ERROR, "the resp packet is not a remote resp.")
            return

        if packet['frame_type'] == 'API_REMOTE_AT_RESP':
            if packet['cmd_id_str'] == 'ATIO':
                self.on_message(address, packet['resp_body']['dio'], packet['resp_body']['state'], 'dio')
            elif packet['cmd_id_str'] == 'ATAD':
                self.on_message(address, packet['resp_body']['src'], packet['resp_body']['value'], 'adc')

        # Data sent through the serial connection of the remote radio
        if packet['frame_type'] == 'API_DATA_PACKET':

            # Some streams arrive split in different packets
            # we buffer the data until we get an EOL
            self.buffer[address] = self.buffer.get(address,'') + packet['data']
            count = self.buffer[address].count('\n')
            if (count):
                lines = self.buffer[address].splitlines()
                try:
                    self.buffer[address] = lines[count:][0]
                except:
                    self.buffer[address] = ''
                for line in lines[:count]:
                    line = line.rstrip()
                    try:
                        port, value = line.split(':', 1)
                    except:
                        value = line
                        port = self.default_port_name
                    self.on_message(address, port, value, 'data')


    #oliver add type: dio/adc/data
    def on_message(self, address, port, value, type):
        """
        Hook for outgoing messages.
        """
        None

    def send_message (self, type, address, msg, port = b'\x0c'):
        """
        Sends a message to a remote radio
        """
        self.log(logging.DEBUG, 'send_message type: %s'%type)

        try:
            addr_len = len(address)
            address = binascii.unhexlify(address)

            if len(port) > 1:
                port = globals()[port]

            if type == 'dio':
                #number = struct.pack('< B',port)
                rw = GPIO_RD
                value = PIN_LOW
                if msg is not None:
                    rw = GPIO_WR
                    value = PIN_LOW if int(msg) == 0 else PIN_HIGH
                if addr_len > 4:
                    self.meshbee.API_REMOTE_AT_REQ(cmd_id = ATIO, dest_addr64 = address, rw = rw, dio=port, state=value)
                else:
                    self.meshbee.API_REMOTE_AT_REQ(cmd_id = ATIO, dest_addr = address, rw = rw, dio=port, state=value)
                self.log(logging.DEBUG, "send remote_at cmd: ATIO at %s "% DIO_name_map[port])
                return True
            elif type == 'adc':
                src = port
                if addr_len > 4:
                    self.meshbee.API_REMOTE_AT_REQ(cmd_id = ATAD, dest_addr64=address, src = src)
                else:
                    self.meshbee.API_REMOTE_AT_REQ(cmd_id = ATAD, dest_addr=address, src = src)
                self.log(logging.DEBUG, "send remote_at cmd: ATAD at %s"% AIO_name_map[src])
                return True
            elif type == 'data':
                print msg
                msg_len = len(msg)
                if addr_len > 4:
                    self.meshbee.API_DATA_PACKET(option = b'\x00', data = msg, data_len = struct.pack('> B', msg_len), dest_addr64 = address)
                else:
                    self.meshbee.API_DATA_PACKET(option = b'\x00', data = msg, data_len = struct.pack('> B', msg_len), dest_addr = address)
                self.log(logging.DEBUG, "sent data: %s"% msg)
                return True
            elif type == 'rpc':
                pass

        except Exception,e:
            print e
            pass

        return False



Factory.register(MeshBeeWrapper)

