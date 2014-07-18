#   Python Library for Mesh Bee
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
#
#
#   This library refers to the implementation of xbee, thanks to the contributors.

import threading
import struct
import time
import binascii
import logging
import types


AT_PARAM_LEN = 8
API_DATA_LEN = 20

GPIO_RD = b'\x01'
GPIO_WR = b'\x00'

REG_RD = b'\x00'
REG_WR = b'\x01'

PIN_HIGH = b'\x01'
PIN_LOW  = b'\x00'

API_START_DELIMITER = b'\x7e'

#AT commands
ATRB = b'\x30'  # reboot
ATPA = b'\x32'  # power up action, for coo:powerup re-form the network; for rou:powerup re-scan networks
ATAJ = b'\x34'  # for rou&end, auto join the first network in scan result list
ATRS = b'\x36'  # re-scan radio channels to find networks
ATLN = b'\x38'  # list all network scaned
ATJN = b'\x40'  # network index which is selected to join,MAX_SINGLE_CHANNEL_NETWORKS = 8
ATLA = b'\x42'  # list all nodes of the whole network, this will take a little more time
ATTM = b'\x44'  # tx mode, 0: broadcast; 1:unicast
ATDA = b'\x46'  # unicast dst addr
ATBR = b'\x48'  # baud rate for uart1
ATQT = b'\x50'  # query on-chip temperature
ATQV = b'\x52'  # query on-chip voltage
ATIF = b'\x54'  # show information of the node
ATAP = b'\x56'  # enter API mode
ATEX = b'\x58'  # exit API mode,end data mode
ATOT = b'\x60'  # ota trigger, trigger upgrade for unicastDstAddr
ATOR = b'\x62'  # ota rate, client req period
ATOA = b'\x64'  # ota abort
ATOS = b'\x66'  # ota status poll
ATTP = b'\x68'  # for test
ATIO = b'\x70'  # set IOs
ATAD = b'\x72'  # read ADC value from AD1 AD2 AD3 AD4

AT_name_map = \
{
    b'\x30': 'ATRB',
    b'\x32': 'ATPA',
    b'\x34': 'ATAJ',
    b'\x36': 'ATRS',
    b'\x38': 'ATLN',
    b'\x40': 'ATJN',
    b'\x42': 'ATLA',
    b'\x44': 'ATTM',
    b'\x46': 'ATDA',
    b'\x48': 'ATBR',
    b'\x50': 'ATQT',
    b'\x52': 'ATQV',
    b'\x54': 'ATIF',
    b'\x56': 'ATAP',
    b'\x58': 'ATEX',
    b'\x60': 'ATOT',
    b'\x62': 'ATOR',
    b'\x64': 'ATOA',
    b'\x66': 'ATOS',
    b'\x68': 'ATTP',
    b'\x70': 'ATIO',
    b'\x72': 'ATAD',
}

### DIOs (value refers to suli.h)
D0   = b'\x00'
D1   = b'\x01'
D2   = b'\x02'
D3   = b'\x03'
D4   = b'\x04'
D5   = b'\x05'
D6   = b'\x06'
D7   = b'\x07'
D8   = b'\x08'
D9   = b'\x09'
D10  = b'\x0A'
D11  = b'\x0B'
D12  = b'\x0C'
D13  = b'\x0D'
D14  = b'\x0e'
D15  = b'\x0f'
D16  = b'\x10'
D17  = b'\x11'
D18  = b'\x12'
D19  = b'\x13'
D20  = b'\x14'
DO0  = b'\x21'
DO1  = b'\x22'

DIO_name_map = \
{
    b'\x00': 'D0' ,
    b'\x01': 'D1' ,
    b'\x02': 'D2' ,
    b'\x03': 'D3' ,
    b'\x04': 'D4' ,
    b'\x05': 'D5' ,
    b'\x06': 'D6' ,
    b'\x07': 'D7' ,
    b'\x08': 'D8' ,
    b'\x09': 'D9' ,
    b'\x0A': 'D10',
    b'\x0B': 'D11',
    b'\x0C': 'D12',
    b'\x0D': 'D13',
    b'\x0e': 'D14',
    b'\x0f': 'D15',
    b'\x10': 'D16',
    b'\x11': 'D17',
    b'\x12': 'D18',
    b'\x13': 'D19',
    b'\x14': 'D20',
    b'\x21': 'DO0',
    b'\x22': 'DO1'
}

### Analog IOs (value refers to the macros defines in Jennic peripheral API user guide )
A1 = b'\x00'
A2 = b'\x01'
A3 = b'\x02'
A4 = b'\x03'
TEMP = b'\x04'
VOL  = b'\x05'

AIO_name_map = \
{
    b'\x00': 'A1',
    b'\x01': 'A2',
    b'\x02': 'A3',
    b'\x03': 'A4',
    b'\x04': 'TEMP',
    b'\x05': 'VOL',
}


#################python2to3###################
"""
python2to3.py

By Paul Malmsten, 2011

Helper functions for handling Python 2 and Python 3 datatype shenanigans.
"""

def byteToInt(byte):
    """
    byte -> int

    Determines whether to use ord() or not to get a byte's value.
    """
    if hasattr(byte, 'bit_length'):
        # This is already an int
        return byte
    return ord(byte) if hasattr(byte, 'encode') else byte[0]

def intToByte(i):
    """
    int -> byte

    Determines whether to use chr() or bytes() to return a bytes object.
    """
    return chr(i) if hasattr(bytes(), 'encode') else bytes([i])

def stringToBytes(s):
    """
    string -> bytes

    Converts a string into an appropriate bytes object
    """
    return s.encode('ascii')

###############################################
class APIFrame:
    """
    Represents a frame of data to be sent to or which was received
    from an MeshBee device
    """

    START_BYTE = API_START_DELIMITER
    frame_type = None

    def __init__(self, data=b''):
        if len(data) > 0:
            self.frame_type = data[0]
            self.data = data[1:]
        self.raw_data = b''

    def checksum(self):
        """
        checksum: None -> single checksum byte

        checksum adds all bytes of the binary
        """
        total = 0

        # Add together all bytes
        for byte in self.data:
            total += byteToInt(byte)

        # Only keep the last byte
        total = total & 0xFF

        return intToByte(total)

    def verify(self, chksum):
        return self.checksum() == chksum

    def len_bytes(self):
        """
        len_data: None -> 16-bit integer length, two bytes

        len_bytes counts the number of bytes to be sent and encodes the
        data length in two bytes, little-endian (lest significant first).
        """
        count = len(self.data)
        return struct.pack("< B", count)   #little-endian

    def output(self):
        """
        output: None -> valid API frame (binary data)

        output will produce a valid API frame for transmission to an
        MeshBee module.
        """
        # start is one byte long, length is two bytes
        # data is n bytes long (indicated by length)
        # chksum is one byte long
        data = APIFrame.START_BYTE + self.len_bytes() + self.frame_type + self.data + self.checksum()

        return  data

    def fill(self, byte):
        """
        fill: byte -> None

        Adds the given raw byte to this APIFrame.
        """
        self.raw_data += intToByte(byteToInt(byte))

    def remaining_bytes(self):
        remaining = 3

        if len(self.raw_data) >= 3:
            # First two bytes are the length of the data
            raw_len = self.raw_data[1]
            data_len = struct.unpack("< B", raw_len)[0]

            remaining += data_len

            # Don't forget the checksum
            remaining += 1

        return remaining - len(self.raw_data)

    def parse(self):
        """
        parse: None -> None

        Given a valid API frame, parse extracts the data contained
        inside it and verifies it against its checksum
        """
        if len(self.raw_data) < 3:
            ValueError("parse() may only be called on a frame containing at least 3 bytes of raw data (see fill())")

        # First two bytes are the length of the data
        raw_len = self.raw_data[1]

        # Unpack it
        data_len = struct.unpack("< B", raw_len)[0]

        # mark the frame type
        self.frame_type = self.raw_data[2]

        # Read the data
        data = self.raw_data[3:3 + data_len]
        chksum = self.raw_data[-1]


        # Checksum check
        self.data = data
        if not self.verify(chksum):
            raise ValueError("Invalid checksum")

class ThreadQuitException(Exception):
    pass

class CommandFrameException(KeyError):
    pass

class MeshBee(threading.Thread):
    """
    communicate with Mesh Bee through the serial interface in API mode
    """

    api_requests = \
    {
        'API_LOCAL_AT_REQ':
            [{'name': 'id',                 'len': 1,             'default': b'\x08'},
             {'name': 'frame_id',           'len': 1,             'default': b'\x01'},
             {'name': 'cmd_id',             'len': 1,             'default': b'\x00'},
             {'name': 'at_req_body',        'len': None,          'default': None   }],
        'API_REMOTE_AT_REQ':
            [{'name': 'id',                 'len': 1,             'default': b'\x17'},
             {'name': 'frame_id',           'len': 1,             'default': b'\x00'},
             {'name': 'option',             'len': 1,             'default': b'\x00'},
             {'name': 'cmd_id',             'len': 1,             'default': b'\x00'},
             {'name': 'at_req_body',        'len': None,          'default': None   },
             {'name': 'dest_addr',          'len': 2,             'default': b'\xff\xfe'},
             {'name': 'dest_addr64',        'len': 8,             'default': b'\x00'*8}],
        'API_DATA_PACKET':
            [{'name': 'id',                 'len': 1,             'default': b'\x02'},
             {'name': 'frame_id',           'len': 1,             'default': b'\x00'},
             {'name': 'option',             'len': 1,             'default': b'\x00'},
             {'name': 'dest_addr',          'len': 2,             'default': b'\xff\xfe'},
             {'name': 'dest_addr64',        'len': 8,             'default': b'\x00'*8},
             {'name': 'data_len',           'len': 1,             'default': b'\x00'},
             {'name': 'data',               'len': None,          'default': b'\x00'}],
    }

    at_req_body = \
    {
        b'\x00':  #default format
            [{'name': 'set',                 'len': 1,             'default': REG_RD},
             {'name': 'reg_value',           'len': 2,             'default': b'\x00\x00'},
             {'name': 'dummy',               'len': 1,             'default': b'\x00'}],
        ATIO:
            [{'name': 'rw',                 'len': 1,             'default': GPIO_RD},
             {'name': 'dio',                'len': 1,             'default': D12},
             {'name': 'state',              'len': 1,             'default': PIN_LOW},
             {'name': 'dummy',               'len': 1,             'default': b'\x00'}],
        ATAD:
            [{'name': 'src',                'len': 1,             'default': TEMP},
             {'name': 'value',              'len': 2,             'default': b'\x00'*2},
             {'name': 'dummy',               'len': 1,             'default': b'\x00'}]
    }

    api_responses = \
    {
        b'\x88':
            {'name': 'API_LOCAL_AT_RESP',
             'structure':
                [{'name': 'frame_id',         'len': 1,                 'type':'dec'},
                 {'name': 'cmd_id',           'len': 1,                 'type':'hex'},
                 {'name': 'status',           'len': 1,                 'type':'hex'},
                 {'name': 'resp_body',        'len': 20,                'type':'raw'}],
             'parsing':[('resp_body', lambda me,original: me._parse_at_resp(original))]
            },
        b'\x97':
            {'name': 'API_REMOTE_AT_RESP',
             'structure':
                [{'name': 'frame_id',         'len': 1 ,                'type':'dec'},
                 {'name': 'cmd_id',           'len': 1 ,                'type':'hex'},
                 {'name': 'status',           'len': 1 ,                'type':'hex'},
                 {'name': 'src_addr',         'len': 2 ,                'type':'hex'},
                 {'name': 'src_addr64',       'len': 8 ,                'type':'hex'},
                 {'name': 'body_len',         'len': 1 ,                'type':'dec'},
                 {'name': 'resp_body',        'len': 20,                'type':'raw'}],
             'parsing':[('resp_body', lambda me,original: me._parse_at_resp(original))]
            },
        b'\x02':
            {'name': 'API_DATA_PACKET',
             'structure':
                [{'name': 'frame_id',         'len': 1 ,                'type':'dec'},
                 {'name': 'option',           'len': 1 ,                'type':'dec'},
                 {'name': 'src_addr',         'len': 2 ,                'type':'hex'},
                 {'name': 'src_addr64',       'len': 8 ,                'type':'hex'},
                 {'name': 'data_len',         'len': 1 ,                'type':'dec'},
                 {'name': 'data',             'len': lambda info: info['data_len'], 'type':'raw'}],
            }
    }



    def __init__ (self, serial, logger, callback=None):
        """
        serial: instance of Serial (pyserial)
        logger: instance of logging.Logger
        """
        super(MeshBee, self).__init__()
        self.serial = serial
        self.logger = logger
        self._thread_continue = False

        if callback:
            self._callback = callback
            self._thread_continue = True
            self.start()

    def __log (self, level, msg):
        if self.logger:
            self.logger.log(level, msg)

    def halt (self):
        if self._callback:
            self._thread_continue = False
            self.join()

    def run (self):
        self.make_sure_api_mode()
        while True:
            try:
                formatted_frame = self.read_frame()
                self._callback(formatted_frame)
            except ThreadQuitException:
                break

    def make_sure_api_mode (self):
        self.serial.write('+++\r\n')
        time.sleep(0.1)
        self.serial.write('ATAP\r\n')
        time.sleep(0.1)
        self.serial.flushInput()
        self.serial.flushOutput()


    ############################# read response ##############################
    def _read_raw_frame (self):
        frame = APIFrame()

        while True:
            if self._callback and not self._thread_continue:
                raise ThreadQuitException

            if self.serial.inWaiting() == 0:
                time.sleep(.01)
                continue

            byte = self.serial.read()
            #print binascii.hexlify(byte)

            if byte != APIFrame.START_BYTE:
                continue

            if len(byte) == 1:
                frame.fill(byte)

            while(frame.remaining_bytes() > 0):
                byte = self.serial.read()
                #print binascii.hexlify(byte)
                if len(byte) == 1:
                    frame.fill(byte)

            try:
                # Try to parse and return result
                frame.parse()

                # Ignore empty frames
                if len(frame.data) == 0:
                    frame = APIFrame()
                    continue
                return frame
            except ValueError:
                # Bad frame, so restart
                frame = APIFrame()

    def _split_response(self, packet_id, data):
        """
        _split_response: binary data -> {'id':str,
                                         'param':binary data,
                                         ...}

        _split_response takes a data packet received from an MeshBee device
        and converts it into a dictionary. This dictionary provides
        names for each segment of binary data as specified in the
        api_responses spec.
        """
        # Fetch the first byte, identify the packet
        # If the spec doesn't exist, raise exception
        try:
            packet = self.api_responses[packet_id]
        except KeyError:
            raise KeyError("Unrecognized response packet with id byte {0}".format(packet_id))

        # Current byte index in the data stream
        index = 0

        # Result info
        info = {'frame_type':packet['name']}
        packet_spec = packet['structure']

        # Parse the packet in the order specified
        for field in packet_spec:
            if field['len'] is not None:
                # Store the number of bytes specified

                # Are we trying to read beyond the last data element?
                f_len = field['len']
                if type(field['len']) == types.FunctionType:
                    f_len = field['len'](info)

                if index + f_len > len(data):
                    raise ValueError(
                        "Response packet was shorter than expected")

                field_data = data[index:index + f_len]
                if field['type'] == 'dec':
                    info[field['name']] = struct.unpack("> B", field_data)[0]
                elif field['type'] == 'hex':
                    info[field['name']] = binascii.hexlify(field_data)
                else:
                    info[field['name']] = field_data

                index += f_len
            # If the data field has no length specified, store any
            #  leftover bytes and quit
            else:
                field_data = data[index:]

                # Were there any remaining bytes?
                if field_data:
                    # If so, store them
                    info[field['name']] = field_data
                    index += len(field_data)
                break

        # If there are more bytes than expected, raise an exception
        if index < len(data):
            raise ValueError(
                "Response packet was longer than expected; expected: %d, got: %d bytes" % (index,
                                                                                           len(data)))

        # Apply parsing rules if any exist
        if 'parsing' in packet:
            for parse_rule in packet['parsing']:
                # Only apply a rule if it is relevant (raw data is available)
                if parse_rule[0] in info:
                    # Apply the parse function to the indicated field and
                    # replace the raw data with the result
                    info[parse_rule[0]] = parse_rule[1](self, info)

        return info

    def _parse_at_resp (self, info):
        resp_body = {}
        data = info['resp_body']
        try:
            info['cmd_id_str'] = AT_name_map[binascii.unhexlify(info['cmd_id'])]
        except:
            info['cmd_id_str'] = 'Unknown'

        if info['cmd_id'] == binascii.hexlify(ATIO):
            resp_body['rw']     = 'r' if data[0] == GPIO_RD else 'w'
            resp_body['dio']    = DIO_name_map[data[1]]
            resp_body['state']  = struct.unpack('> B', data[2])[0]
        elif info['cmd_id'] == binascii.hexlify(ATAD):
            resp_body['src']     = AIO_name_map[data[0]]
            resp_body['value']   = struct.unpack('> H', data[1:3])[0]
        else:
            resp_body['value']   = struct.unpack('> H', data[0:2])[0]

        return resp_body


    def read_frame (self):
        frame = self._read_raw_frame()
        return self._split_response(frame.frame_type, frame.data)

    ############################# send requests ##############################
    def _build_command (self, req, **kwargs):
        try:
            cmd_spec = self.api_requests[req]
        except:
            raise NotImplementedError("Bad request type: %s" % req)

        packet = b''
        cmd_id = b'\x00'

        for field in cmd_spec:
            try:
                # Read this field's name from the function arguments dict
                data = kwargs[field['name']]
                if field['name'] == 'cmd_id':
                    cmd_id = data
                if field['len'] and not field['len'] == len(data):
                    self.__log(logging.WARNING, 'field %s length is not %d, expand with 00' % (field['name'], field['len']))
                    data += (b'\x00' * (field['len']-len(data)))

            except KeyError:
                # Data wasn't given
                # Only a problem if the field has a specific length
                if field['len'] is not None:
                    # Was a default value specified?
                    default_value = field['default']
                    if default_value:
                        # If so, use it
                        data = default_value
                    else:
                        # Otherwise, fail
                        raise KeyError(
                            "The expected field %s of length %d was not provided"
                            % (field['name'], field['len']))
                else:
                    # No specific length, ignore it
                    if field['name'] == 'at_req_body':
                        if cmd_id not in self.at_req_body.keys():
                            cmd_id = b'\x00'
                        data = b''
                        for f in self.at_req_body[cmd_id]:
                            try:
                                sub_data = kwargs[f['name']]
                            except KeyError:
                                sub_data = f['default']
                            if sub_data:
                                data += sub_data
                    else:
                        data = None

            # Ensure that the proper number of elements will be written
            if field['len'] and len(data) != field['len']:
                raise ValueError(
                    "The data provided for '%s' was not %d bytes long"\
                    % (field['name'], field['len']))

            # Add the data to the packet, if it has been specified
            # Otherwise, the parameter was of variable length, and not given
            if data:
                packet += data

        return packet



    def _write (self, data):
        frame = APIFrame(data).output()
        #print "framelen:",len(frame)
        #print binascii.hexlify(frame)
        self.serial.write(frame)

    def send(self, req, **kwargs):
        """
        When send is called with the proper arguments, an API request
        will be written to the serial port for this Mesh Bee device
        containing the proper instructions and data.

        This method must be called with named arguments in accordance
        with the api_requests specification. Arguments matching all
        field names other than those in reserved_names (like 'id' and
        'order') should be given, unless they are of variable length
        (of 'None' in the specification. Those are optional).
        """
        # Pass through the keyword arguments
        self._write(self._build_command(req, **kwargs))

    def __getattr__(self, name):
        """
        If a method by the name of a valid api command is called,
        the arguments will be automatically sent to an appropriate
        send() call
        """

        # If api_commands is not defined, raise NotImplementedError\
        #  If its not defined, _getattr__ will be called with its name
        if name == 'api_requests':
            raise NotImplementedError("Use a derived class which defines in 'api_requests'.")

        # Is shorthand enabled, and is the called name a command?
        if name in self.api_requests:
            # If so, simply return a function which passes its arguments
            # to an appropriate send() call
            return lambda **kwargs: self.send(name, **kwargs)
        else:
            raise AttributeError("MeshBee has no attribute '%s'" % name)













