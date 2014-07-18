#!/usr/bin/python

#   Pan to MQTT gateway
#   Copyright (C) 2014 by seeedstudio
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

from plugins.base import PluginBase
import threading
import time
from factory import Factory
from pan.mesh_bee import *


class QueryMeshBee(PluginBase):
    """
    Do something at intervals
    """

    timer = None

    def start (self):
        print '===========QueryMeshBee=========='
        self.timer = threading.Timer(self.config['interval'], self.query)
        self.timer.start()

    def query (self):
        print "query mesh bee"

        if 'dio' in self.config:
            for addr, dio_list in self.config['dio'].items():
                for dio in dio_list:
                    pin = globals()[dio]
                    self.send_to_pan ('dio', addr, None, port=pin)

        if 'adc' in self.config:
            for addr, adc_list in self.config['adc'].items():
                for adc in adc_list:
                    pin = globals()[adc]
                    self.send_to_pan ('adc', addr, None, port=pin)

        self.timer = threading.Timer(self.config['interval'],self.query)
        self.timer.start()

    def cleanup (self):
        if self.timer:
            self.timer.cancel()


Factory.register(QueryMeshBee)

