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


class Timer(PluginBase):
    """
    Do something at intervals
    """

    timer = None

    def start (self):
        print '===========Timer=========='
        self.timer = threading.Timer(self.config['interval'], self.broadcast_time)
        self.timer.start()

    def broadcast_time (self):
        print "broadcast_time"
        #self.send_to_pan ('data', '0013a200407916c5', 'date=2014-07-01')
        #self.send_to_pan ('data', '000000000000ffff', 'date=2014-07-01')
        self.send_to_pan ('data', '00158d00003552b7', 'date=2014-07-01\r\n')

        self.timer = threading.Timer(self.config['interval'],self.broadcast_time)
        self.timer.start()

    def cleanup (self):
        if self.timer:
            self.timer.cancel()


Factory.register(Timer)
