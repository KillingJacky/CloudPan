#!/usr/bin/python

#   plugin for uploading data to xively.com
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

#   dependence:
#   xively-python: pip install xively-python --pre

from plugins.base import PluginBase
import threading
import time, datetime
import xively
import requests
from factory import Factory


class Xively(PluginBase):
    """
    * if you dont have the control of mosquitto broker:
        you can use this plugin to upload topic to xively but with some performance drawback
    * if you have the broker control permission:
        using the bridge functionality to upload data to xively is a better choice
    """

    api = None
    feed = None
    topics = []
    last_time = datetime.datetime.now()

    def start (self):
        print '===========xively==========='
        self.api = xively.XivelyAPIClient(self.config['api_key'])
        self.feed = self.api.feeds.get(int(self.config['feed_id']))
        self.topics = self.config['upload_topics']
        if not isinstance(self.topics, list):
            self.topics = [self.topics]
        
    def get_datastream(self, chnl):
        try:
            datastream = self.feed.datastreams.get(chnl)
            return datastream
        except:
            datastream = self.feed.datastreams.create(chnl)
            return datastream

    def pre_publish (self, t, v_filtered, v_raw):
        if datetime.datetime.now() - self.last_time < datetime.timedelta(seconds=self.config['interval']):
            return
        if t in self.topics and self.feed:
            try:
                datastream = self.get_datastream(t.replace('/','_'))
                datastream.max_value = None
                datastream.min_value = None
                datastream.current_value = v_filtered
                datastream.at = datetime.datetime.utcnow()
                datastream.update()
                self.last_time = datetime.datetime.now()
            except requests.HTTPError as e:
                print "HTTPError({0}): {1}".format(e.errno, e.strerror)
            except Exception,e:
                print e
        

Factory.register(Xively)

