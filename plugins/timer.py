#!/usr/bin/python

#   Heartbeat Collection and Analyser
#   Copyright (C) 2014 by seeedstudio
#   Author: Oliver wang 
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
import sqlite3 as database
from datetime import datetime
import yaml

class Timer(PluginBase):
    """
    Do something at intervals
    """

    def __init__(self):
        #connect to database(sqlite is multi-thread unsafe,shared globle connection)
        try:
            print "Connecting to sqlite datebase ..."
            self.conn = database.connect('gateway.db')  #check_same_thread = False
            self.cur = self.conn.cursor()
        except database.Error, e:
            print "Can't connect to database: %s" % e
            pass            
    
    def heartbeat_add_item(self, mac, type, payload, heartbeatTime):  
        try:                   
            self.cur.execute("INSERT INTO heartbeat VALUES(?,?,?,?)", (mac, type, payload, heartbeatTime))            
            self.conn.commit()
        except database.Error, e:
            print "class:Timer, function:heartbeat_add_item, can not insert,error: %s" % e  
            pass

    def heartbeat_update_item(self, mac, type, payload, heartbeatTime):
        try:
            self.cur.execute("UPDATE heartbeat SET payload = ?, heartbeatTime = ? WHERE mac = ? AND type = ?", (payload, heartbeatTime, mac, type))
            self.conn.commit()
        except database.Error, e:
            print "class:Timer, function:heartbeat_update_item, can not update,error: %s" % e 
            pass
    
    def get_heartbeat_by_mac_and_type(self, mac, type):
        
        heartbeatItem = None
        try:             
            self.cur.execute("select * from heartbeat where heartbeat.mac = ? and heartbeat.type = ?", (mac, type))             
            heartbeatItem = self.cur.fetchone()
        except database.Error, e:
            print "class:Timer, function:get_heartbeat_by_mac, can not search,error: %s" % e
            pass
        finally:
            return heartbeatItem

    def start (self):
        print '===========Timer Task=========='
        self.timer = threading.Timer(self.config['p_interval'], self.interval_task)
        self.timer.start()

    def interval_task (self):                 
        '''
        database
        '''
        try:            
            #print 'Heartbeat Analyser'  
            conn = database.connect('gateway.db')
            cur = conn.cursor()
            cur.execute('SELECT * FROM heartbeat WHERE heartbeat.mac is not null')
            all_items = cur.fetchall()
            for row in all_items:
                _mac = row[0]
                _type = row[1]
                _matchKey = row[2]
                _payload = row[3]
                heartbeat_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                #judge if this node[src] is off-line
                offline_threshold = self.config['offline_threshold']                  
                now = datetime.now()            
                if (now - heartbeat_time).seconds > offline_threshold:
                    print "--------------node:%s is offline------------" % _mac 
                    topic = self.global_config['const_topic']['topic_offline_alert'] + '/' + self.global_config['mqtt']['client_id']
                    self.send_to_mqtt(topic, str(_mac))                 
                    #delete the offline heartbeat item                 
                    cur.execute('DELETE FROM heartbeat WHERE heartbeat.mac = ? AND heartbeat.matchKey = ?', (_mac, _matchKey))
                    conn.commit()
                else:
                    #process online node[src] item                                                    
                    value_f = float(_payload)
                    value_i = int(value_f)
                    if 'light' == _matchKey:       #this is a light sensor                  
                        light_threshold = self.config['light_threshold']                       
                        if value_i > light_threshold:
                            self.send_to_pan('dio', self.config['notify_node'], 0, 'D0')
                            #print '************************************Bright, turn off light*****************************'
                        else:
                            self.send_to_pan('dio', self.config['notify_node'], 1, 'D0')
                            #print '***********************************Dim, turn on light**********************************'
                    elif 'gas' == _matchKey:
                        gas_threshold = self.config['gas_threshold']
                        if value_i > gas_threshold:
                            self.send_to_pan('dio', self.config['notify_node'], 1, 'D0')
                            #print '*************************Alert: gas concentrations exceeding**************************'
                        else:
                            self.send_to_pan('dio', self.config['notify_node'], 0, 'D0')
            if conn:
                conn.close()
        except Exception, e:
            print "class:Timer, function:interval_task, error:%s" % e
            
        #restart timer         
        self.timer = threading.Timer(self.config['p_interval'], self.interval_task)
        self.timer.start()

    def on_message_from_pan (self, address, key, value, type):                
        '''
        table [mac, data_type, data_value, heartbeat_time]
        if item exsits already, update, otherwise, insert 
        '''
        try:
            #Heartbeat only contain data frame, filter dio/adc here
            if 'data' != type:
                return True                
            print "======================new device heartbeat==========================="
            #connect        
            #print "connecting to database ..."
            conn = database.connect('gateway.db')
            cur = conn.cursor()            
            #fetch
            heartbeat_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #mac and matchKey is the single ID for a heartbeat item
            cur.execute("select * from heartbeat where heartbeat.mac = ? and heartbeat.matchKey = ?", (address, key)) 
            heartbeat_item = cur.fetchone() 
            if heartbeat_item is not None:
                #update                             
                cur.execute("UPDATE heartbeat SET payload = ?, heartbeatTime = ? WHERE mac = ? AND matchKey = ?", (value, heartbeat_time, address, key))
                conn.commit()
                print "update"
            else:
                #insert
                cur.execute("INSERT INTO heartbeat VALUES(?,?,?,?,?)", (address, type, key, value, heartbeat_time))
                conn.commit()
                print "insert"   
            #each time we finish,close connection
            if conn:
                conn.close()  
            return True       
        except database.Error, e:
            print "class:Timer, function:on_message_from_pan, sqlite database,error: %s" % e 
            if conn:
                conn.close()   
            return False 
    
                             
    def cleanup (self):
        if self.timer:
            self.timer.cancel()

Factory.register(Timer)
