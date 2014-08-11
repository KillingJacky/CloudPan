#!/usr/bin/python
# -*- coding:utf-8 -*-
#dependence: paho-mqtt (pip install paho-mqtt)
#            XBee (pip install XBee)
#            PyYAML (pip install PyYaml)
#            pyserial (pip install pyserial)

import os
import sys
import time
import logging
import yaml

from serial import Serial
from factory import *
from pan import *
from filters import *
from plugins import *
from paho.mqtt import client
from daemon import Daemon
import sqlite3 as database 


class PAN2MQTT(Daemon):
    """
    PAN network to MQTT bridge
    Supported PAN radio: XBee, Mesh Bee(from seeedstudio)
    To port a new radio driver, two method must be implemented: on_message, send_message
    """


    def __init__ (self, logger, cfg):
        """
        """
        Daemon.__init__(self,cfg['general']['pidfile'])

        self.logger = logger
        self.config = cfg
        self.mqtt_connected = False
        self.mqtt_subcriptions = {}
        self.downlink_topics = {}
        self.uplink_topics = {}

        self.pan = Factory(self.config['pan']['driver_class'])
        if not self.pan:
            self.__log(logging.ERROR, "Can't instant pan driver")
            sys.exit(2)
        self.pan.logger = logger
        self.pan.on_message = self.on_message_from_pan

        self.stdout = self.config['general']['stdout']
        self.stderr = self.config['general']['stdout']
        self.host = self.config['mqtt']['host']
        self.client_id = self.config['mqtt']['client_id']
        self.mqtt_qos = self.config['mqtt']['qos']
        self.mqtt_retain = self.config['mqtt']['retain']
        self.status_topic = self.config['mqtt']['status_topic']

        self.mqtt_client = client.Client(self.client_id, self.config['mqtt']['clean_session'])
        if self.__try_get_config(self.config['mqtt'], "username", None):
            self.mqtt_client.username_pw_set(self.config['mqtt']['username'], self.config['mqtt']['password'])
        if self.config['mqtt']['set_will']:
            self.mqtt_client.will_set(self.status_topic.format(client_id=self.client_id), "0", self.mqtt_qos, self.mqtt_retain)

        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.on_message = self.on_message_from_mqtt
        self.mqtt_client.on_subscribe = self.on_mqtt_subscribe
        self.mqtt_client.on_log = self.on_mqtt_log

        self.plugins = self.__try_get_config(self.config, 'plugin', None)
        if not isinstance(self.plugins, dict):
            self.plugins = {self.plugins}
        self.plugins_ins = {}

    ### private method
    def __log(self, level, message):
        if self.logger:
            self.logger.log(level, message)


    @staticmethod
    def __try_get_config (parent, key, default):
        try:
            return parent[key]
        except:
            return default

    def __parse_nodes (self):
        self.downlink_topics = {}
        self.uplink_topics = {}

        if self.config['pan']['nodes']:
            for mac,mac_obj in self.config['pan']['nodes'].items():
                for topic,topic_content in mac_obj.items():
                    topic = topic.format(client_id=self.client_id)
                    if topic_content['dir'] == "uplink":
                        self.uplink_topics[(mac, topic_content['match_key'])] = (topic,self.__try_get_config(topic_content,'filter',None))
                    elif topic_content['dir'] == "downlink":
                        self.downlink_topics[topic] = (mac, topic_content)
                    else:
                        self.__log(logging.ERROR, "Unknown 'dir'")
        

    def __sub_downlink_topics (self):
        if not self.mqtt_connected:
            return
        for t in self.downlink_topics:
            rc, mid = self.mqtt_client.subscribe(t, self.mqtt_qos)
            self.mqtt_subcriptions[mid] = t
            self.__log(logging.INFO, "Sent subscription request to topic %s" % t)
        
        
    def __filter (self, input, filter_config):
        try:
            filter = Factory(filter_config['type'])
            if filter:
                filter.configure(filter_config['parameters'])
                if filter.validate():
                    return filter.process(input)
        except:
            pass
        return input

    #response topic list to client which requires this
    def __resp_topic_list(self, dst_topic):
        '''
        Broadcast gateway information when the gateway thread is starting 
        '''             
        str_topic_holder = ''     
        if self.config['pan']['nodes']:
            for mac,mac_obj in self.config['pan']['nodes'].items():
                for topic,topic_content in mac_obj.items():
                    topic = topic.format(client_id=self.client_id)
                    if topic_content['dir'] == "uplink" and topic_content['type'] != "listening":
                        str_topic_holder = str_topic_holder + topic + "@"
                        
        print "topic list:" + str_topic_holder
        self.mqtt_client.publish(dst_topic, str_topic_holder, 2)               
        
        
    ###
    def on_mqtt_connect (self, client, userdata, flags, rc):
        if rc == 0:
            self.__log(logging.INFO, "Connected to MQTT broker: %s" % self.host)
            self.mqtt_client.publish(self.status_topic.format(client_id=self.client_id), "1")
            self.mqtt_connected = True
            self.__sub_downlink_topics()
        else:
            self.__log(logging.ERROR, "Could not connect to MQTT broker: %s" % self.host)
            self.__log(logging.ERROR, "Error code: %d" % rc)
            self.mqtt_connected = False

    def on_mqtt_disconnect (self, client, userdata, rc):
        self.mqtt_connected = False
        self.__log(logging.INFO, "Disconnected from MQTT broker: %s"%self.host)
        self.__log(logging.INFO, "Return code: %d"%rc)
        if rc!=0:
            self.__log(logging.ERROR, "Unexpected disconnect, waiting reconnect...")

    def on_mqtt_subscribe (self,client, userdata, mid, granted_qos):
        topic = self.mqtt_subcriptions.get(mid, "Unknown")
        self.__log(logging.INFO, "Sub to topic %s confirmed"%topic)

    def on_mqtt_log (self, client, userdata, level, buf):
        self.__log(logging.DEBUG, buf)

    def on_message_from_pan (self, mac, key, value, type):
        self.__log(logging.INFO, "Received message from PAN: %s, %s:%s" % (mac, key, value))

        #walk over plugins and determin whether to drop
        '''
        there are two callback in each plugin
        1.on_message_from_pan abstract function in base
        description: do something when receives pan event 
        2.pre_publish
        description: do something before publish to broker        
        '''
        for name,p in self.plugins_ins.items():
            if not p.on_message_from_pan(mac, key, value, type):            
                return False

        #search the topic
        try:
            if self.uplink_topics[(mac,key)]:
                topic, filter = self.uplink_topics[(mac,key)]

                #apply the filter
                value_f = value
                if filter:
                    value_f = self.__filter(value, filter)

                #walk over plugins and call the callback which watches on the publishment
                for name,p in self.plugins_ins.items():
                    if p.pre_publish:
                        p.pre_publish(topic, value_f, value)

                #publish the topic
                self.__log(logging.INFO, "Publishing to topic: %s"%topic)
                self.mqtt_client.publish(topic, value_f, self.mqtt_qos, self.mqtt_retain)
        except KeyError, e:
            self.__log(logging.WARNING, "Received message unrecognized: %s" % e)

    def on_message_from_mqtt (self,client, userdata, message):
        self.__log(logging.INFO, "Received message from MQTT: %s: %s, qos %d" % (message.topic,message.payload,message.qos))

        #walk over plugins and determin whether to drop
        for name,p in self.plugins_ins.items():
            if not p.on_message_from_mqtt(message.topic, message.payload, message.qos):
                return False

        #search the topic
        if self.downlink_topics[message.topic]:
            mac, topic = self.downlink_topics[message.topic]

            #apply the filters
            if self.__try_get_config(topic, 'filter', None):
                value = self.__filter(message.payload, topic['filter'])
            else:
                value = message.payload

            #handle the topic types
            if topic['type'] == 'dio':
                self.pan.send_message('dio', mac, value, port = topic['dio_num'])
                #self.__log(logging.DEBUG, "sent dio message")
            elif topic['type'] == 'data':
                self.pan.send_message('data', mac, value)
            elif topic['type'] == 'rpc':            
                pass
            elif topic['type'] == 'listening':
                #to specified client
                self.__resp_topic_list(str(value))
            else:
                self.__log(logging.ERROR, "Unknown downlink handler type: %s" % topic['type'])
                return
        else:
            self.__log(logging.ERROR,"Received an unknown topic '%s' from mqtt" % message.topic)
            return

    def do_reload (self):
        self.__log(logging.DEBUG, "Reload not implemented now")
          
                  
    def run (self):
        
        self.__log(logging.INFO, "Starting Pan2Mqtt %s" % self.config['general']['version'])
                         
        #parse nodes, up/down-link channels
        self.__parse_nodes()
                     
        #connect mqtt
        self.mqtt_client.connect(self.host, self.config['mqtt']['port'], self.config['mqtt']['keepalive'])
        sec=0
        while True:
            if self.mqtt_connected:
                break
            else:
                self.mqtt_client.loop()
                sec=sec+1
                if sec > 60:
                    self.stop()
                    sys.exit(2)

        #connect pan radio
        try:
            serial = Serial(self.config['pan']['port'], self.config['pan']['baudrate'])
        except Exception,e:
            self.__log(logging.ERROR, "Can't open serial: %s" % e)
            sys.exit(2)
        self.pan.serial = serial
        if not self.pan.connect():
            self.stop()

        #start the plugins
        for p in self.plugins:
            ins = Factory(p)
            if ins:
                self.plugins_ins[p] = ins
                if self.__try_get_config(self.config['plugin'], p, None):
                    self.plugins_ins[p].config = self.config['plugin'][p]
                    self.plugins_ins[p].global_config = self.config
                self.plugins_ins[p].send_to_pan = self.pan.send_message
                self.plugins_ins[p].send_to_mqtt = self.mqtt_client.publish
                self.plugins_ins[p].start()
            else:
                self.__log(logging.ERROR, "Can not make the instance of %s from factory"%p)

        
        #blocking loop
        try:
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            self.__log(logging.ERROR, "Terminated by user")
            self.cleanup()

    def cleanup (self):
        self.pan.disconnect()
        self.__log(logging.INFO, "Cleaning up...")
        self.mqtt_client.disconnect()
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
        for name, p in self.plugins_ins.items():
            p.cleanup()
        sys.exit()




def resolve_path(path):
    return path if path[0] == '/' else os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


if __name__ == '__main__':
    config_file = './pan2mqtt.yaml'

    fh = file(resolve_path(config_file), 'r')
    config = yaml.load(fh)
    fh.close()

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(config['general']['log_level'])
    logger.addHandler(handler)


    gw = PAN2MQTT(logger, config)


    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            gw.start()
        elif 'stop' == sys.argv[1]:
            gw.stop()
        elif 'restart' == sys.argv[1]:
            gw.restart()
        elif 'reload' == sys.argv[1]:
            gw.reload()
        elif 'foreground' == sys.argv[1]:
            gw.run()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|foreground" % sys.argv[0]
        sys.exit(2)













