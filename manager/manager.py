import os
import json
import time
import socket
import asyncio
import websockets
import logging
import random
import pandas as pd
import sqlite3
import sys

# Constants
MOD_PORT = 12001

# Globals
CONNECTION_TABLE = {}

db_push_q = asyncio.Queue()
lock = asyncio.Lock()

LAST_KEY_COUNT = 0.0
TOTAL_KEYS = 0.0

LINE_LIMIT = 1000
local_content = []
COUNT=0

logging.basicConfig(level=logging.INFO, filename='log_manager.log', filemode='a', format='%(name)s - %(asctime)s - %(levelname)s  - %(message)s')

class sqliteDb(object):
    def __init__(self, db_path):
        self._db_size = 0	
        self._con = sqlite3.connect(db_path, check_same_thread = False)
        self._cur = self._con.cursor()
        KickedOut_sql = """CREATE TABLE kicked_out(
		inIP text NOT NULL,
		extIP text NOT NULL,
		proto text NOT NULL,
		appPort text NOT NULL,
		dir text NOT NULL,
        sport text NOT NULL,
		time real NOT NULL,
		insize integer NOT NULL,
		outsize integer NOT NULL,
        incount integer NOT NULL,
        outcount integer NOT NULL,
        scount integer NOT NULL,
        pcount integer NOT NULL
        );"""

        try:
            self._cur.execute(KickedOut_sql)
            self._con.commit()
        except:
            pass

    def get_count(self):
        try:
            self._cur.execute("SELECT count(*) FROM kicked_out")	
            return self._cur.fetchone()[0]
        except:
            logging.error('Query failed:{}'.format("SELECT count(*)"))
            return False
    
    def insert_db(self, i_key, i_value):
        try:
            l_item = tuple(i_key.split(','))+(i_value['time'], i_value['insize'], i_value['outsize'] , i_value['incount'],\
                 i_value['outcount'],i_value['scount'], i_value['pcount'])
            self._cur.execute("INSERT INTO kicked_out VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(l_item))
            self._con.commit()  
            self._db_size += 1		
            return True
        except:
            logging.error('Insert query failed key:{}, value:{}.'.format(i_key, i_value))
            return False
    

    def delete_db(self, i_key):
        try:
            l_item = tuple(i_key.split(','))
            self._cur.execute("""DELETE FROM kicked_out WHERE inIP = ? AND extIP = ? AND proto = ? AND appPort = ? AND dir = ?""", tuple(l_item))	
            self._con.commit()		
            self.db_size = self.db_size - 1
            return True
        except:
            logging.error('Delete query failed key:{}'.format(i_key))
            return False


    def lookup_key(self, i_key):
        try:
            l_item = tuple(i_key.split(','))
            self._cur.execute("""SELECT * FROM kicked_out WHERE inIP = ? AND extIP = ? AND proto = ? AND appPort = ? AND dir = ?""", tuple(l_item))	
            if len(self._cur.fetchall()):
                return True
            else:
                return False
        except:
            logging.error('Lookup query failed key:{}'.format(i_key))
            return False


    def update_key(self, i_key, i_value):
        try:
            l_item = tuple(i_key.split(','))
            self._cur.execute("""SELECT * FROM kicked_out WHERE inIP = ? AND extIP = ? AND proto = ?\
                 AND appPort = ? AND dir = ? AND sport = ?""", tuple(l_item))	
            l_op = self._cur.fetchone()
            if not l_op is None:                
                l_item =  (i_value['time'], int((i_value['insize']+l_op[-6])/2), int((i_value['outsize']+l_op[-5])/2),int((i_value['incount']+l_op[-4])/2),\
                     int((i_value['outcount']+l_op[-3])/2),int((i_value['scount']+l_op[-2])/2), int((i_value['pcount']+l_op[-1])/2)) + tuple(i_key.split(','))
                self._cur.execute("""UPDATE kicked_out SET time=?,insize=?,outsize=?,incount=?,outcount=?,scount=?, pcount=?\
                     WHERE inIP=? AND extIP=? AND proto=? AND appPort=? AND dir=? AND sport = ?""", tuple(l_item)) 
                self._con.commit()
                return True
            else:
                logging.debug('Inserting key {}.'.format(i_key))
                self.insert_db(i_key, i_value)
        except:
            logging.error('update_key query failed key:{}, value:{}'.format(i_key, i_value))
            return False
    

    def lookup_other(self, i_key, i_value):
        try:        
            temp_string  = "SELECT * FROM kicked_out WHERE "

            for k in i_key:
                temp_string += k+' = ? AND '
        
            temp_string = temp_string[:-4]
            self._cur.execute(temp_string,tuple(i_value))
            return self._cur.fetchall()
        except:
            logging.error('lookup_other query failed key:{}, value:{}'.format(i_key, i_value))
            return None


    def lookup_timed_entries(self, i_time):
        try:
            if not i_time is None:

                temp_string  = "SELECT * FROM kicked_out WHERE time >= {}".format(i_time)
            else:
                temp_string  = "SELECT * FROM kicked_out"


            self._cur.execute(temp_string)
            return self._cur.fetchall()
        except:
            logging.error('lookup_timed_entries query failed for time:{}'.format(i_time))
            return None
	
    def drop_table(self):
        self._cur.execute("DROP TABLE kicked_out")

    def db_close(self):
        self._con.close()

def get_bin(i_count, i_size):
    if i_count > 0 and i_count <=5:
        c='c_0'
    elif i_count > 5 and i_count <=20:
        c='c_1'
    elif i_count > 20 and i_count <=50:
        c='c_2'
    else:
        c='c_3'
        
    if i_size > 0 and i_size <=50:
        s='s_0'    
    elif i_size > 51 and i_size <=100:
        s='s_1'
    elif i_size > 100 and i_size <=250:
        s='s_2'
    else:
        s='s_3'
    return c,s

def get_all_entries():
    ret_list = []
    y = sql.lookup_timed_entries(None)
    if not y is None:
        if len(y) >0 :
            for entry in y:
                try:
                    count = entry[9] + entry[10]
                    size = int((entry[7] + entry[8])/count)
                    count_bin, size_bin = get_bin(count, size)      
                    ret_list.append([entry[4], entry[0], entry[1], entry[2]+'.'+ entry[5],\
                        entry[2]+'.'+ entry[3], count_bin, size_bin])
                except KeyError:
                    logging.error('Unknown direction entries in db.')
    df_w = pd.DataFrame(ret_list)
    df_w.to_csv('entries_'+str(time.time())+'.csv', header=['dir', 'intIP', 'extIP', 'sport', 'dport', 'cntBin', 'sizeBin'],index=False)    

async def write_to_file(i_content):
    global COUNT
    file_name = 'entries_'+str(COUNT)+'.txt'
    logging.info('Writing to {}'.format(file_name))
    with open(file_name, 'w') as writer:
        writer.write('intIP,extIP,proto,dport,dir,sport,incount,outcount,insize,outsize,scount,pcount,time\n')
        writer.writelines(i_content)
    COUNT+=1

# Process connection anomaly event.
def conn_anomaly(i_payload: dict):
    global local_content
    for i,j in i_payload['key_val'].items():
        temp=i+','+str(j['incount'])+','+str(j['outcount'])+','+str(j['insize'])+','+str(j['outsize'])+','\
            +str(j['scount'])+','+str(j['pcount'])+','+str(j['time'])+'\n'
        local_content.append(temp)
    
    if len(local_content) >= LINE_LIMIT:
        asyncio.ensure_future(write_to_file(local_content.copy()))
        local_content.clear()


# Send the event to a gateway.
async def send_gateway_event(gateway, event, data):
    global CONNECTION_TABLE

    msg = {}
    msg['timestamp'] = time.time()
    msg['event'] = event
    msg['sender'] = 'master'
    msg['receiver'] = gateway
    msg['data'] = data

    msg = json.dumps(msg)
    try :
        await CONNECTION_TABLE[gateway].send(msg)
    except:
        logging.error("[#] Send failed.")


# Process msg. 
async def process_msg(msg, module):
    global TOTAL_KEYS, LAST_KEY_COUNT

    msg = json.loads(msg)

    if not ('event' in msg.keys() and 'data' in msg.keys()):
        logging.error("Event not in the message.")
        return
    
    event = msg['event']
    payload = msg['data']

    if event == "EVT_CONN_ANOMALY":
        TOTAL_KEYS += len(payload['key_val'])
        logging.info("Gateway - {} - Data size - {} - Total keys - {}/{}".format(msg['sender'], len(payload['key_val']), TOTAL_KEYS, TOTAL_KEYS - LAST_KEY_COUNT))
        LAST_KEY_COUNT = TOTAL_KEYS
        conn_anomaly(payload)
    elif event == "EVT_BEHV_ANOMALY":
        pass
    elif event == "EVT_QUERY_RESPONSE":
        pass
    elif event == "EVT_GW_DEVICES":
        logging.info("Gateway: {}, devices: {}".format(msg['sender'], payload))
    else:
        logging.error('Unknown event received.')

# Receiver events.
async def recv_module_event(websocket, path):
    global CONNECTION_TABLE

    module = os.path.basename(path)
    logging.info('Module {}, Address {}'.format(module, websocket.remote_address))

    CONNECTION_TABLE[module] = websocket

    try:
        while(True) :
            msg = await websocket.recv()
            logging.debug("Received msg: {}".format(msg))
            await process_msg(msg, websocket)

    except websockets.exceptions.ConnectionClosed:
        del CONNECTION_TABLE[module]
        logging.info('Connection closed by module: {}'.format(module))   

    except:
        logging.info('Exception in recv_module_event')
        logging.info(sys.exc_info())   
        

#sql = sqliteDb("/tmp/db.db")

EVENT_LOOP = asyncio.get_event_loop()
task = websockets.serve(recv_module_event, '0.0.0.0', MOD_PORT)

EVENT_LOOP.run_until_complete(task)
#asyncio.ensure_future(sql_task())

start_time = time.time()

try:
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    #get_all_entries()
    logging.info('Running time {} seconds. Rx keys: {}.'.format(time.time() - start_time, TOTAL_KEYS))
    #sql.db_close()
    logging.info('!!!! Module Closed !!!!.')
