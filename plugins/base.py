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


class PluginBase(object):
    """
    The base class for plugin
    """
    config = None
    global_config = None

    def start (self):
        """
        Hook
        """
        pass

    def send_to_pan (self, type, address, data, dio_num = 0):
        """
        Hook
        """
        pass

    def send_to_mqtt (self, topic, value, qos, retain):
        """
        Hook
        """
        pass

    def on_message_from_pan (self, address, key, value):
        """
        Hook
        Return False to drop the original message
        """
        return True

    def pre_publish (self, topic, value_filtered, value_raw):
        """
        the very time before publish to the mqtt broker
        the value is filtered
        """
        None

    def on_message_from_mqtt (self, topic, payload, qos):
        """
        Hook
        Return False to drop the topic
        """
        return True

    def cleanup (self):
        """
        Hook
        """
        pass




