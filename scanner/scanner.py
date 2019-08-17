import json
import time
import asyncio
import websockets
import os
from threading import Thread, Lock
import ipaddress
import queue
import socket
from random import randint, choice
from scapy.all import IP, TCP, sr1, RandShort
from uuid import getnode as get_mac
import sys

MY_ADDR = "0.0.0.0"
MODULE = 'scanner_'+str(get_mac())

try:
    MOD_IP = sys.argv[1]
except:
    sys.exit('MOD_IP missing. Exiting.')    

MOD_PORT = 4567

COMM_HANDLE = None
SCAN_NETWORKS = None
SCAN_PORTS = None
SCAN_RATE = 1
SPOOFED_NETWORK = "10.2.0.0/16"

# Generate a random ip address from a given network (192.168.0.0/24, 10.0.0.0/30).
def get_ip_address(i_network):
    net = ipaddress.IPv4Network(i_network)
    return net[randint(2, net.num_addresses-2)].exploded

# Class to do tcp scan. Input all the ip & port tuple in queue. Can perform connect and sysn scans.
class tcp_scan(Thread):
    def __init__(self, i_spoofed, i_ip,i_port):
        super(tcp_scan, self).__init__()
        self._ip = i_ip
        self._port = i_port
        self._sip = i_spoofed

    def run(self):
        self._syn_scan()

    def _syn_scan(self):
        p = IP(src = self._sip, dst = self._ip)/TCP(sport=RandShort(), dport=self._port, flags='S')    
        sr1(p, timeout=1, verbose=0)

# Scan routine.
async def scan():

    duration = 5.0
    while True:
        max_ips = 20
        if SCAN_RATE == 1:
            max_ips = 10
            duration = 10.0
        elif SCAN_RATE == 2:
            max_ips = 20
            duration = 5.0
        elif SCAN_RATE == 3:
            max_ips = 30
            duration = 1.0
        elif SCAN_RATE == 0:
            max_ips = randint(20,30)
            duration = randint(10,30)
        else:
            print("[E] Unknown scan parameters.")
            return

        for _ in range(randint(int(max_ips/2), int(max_ips))):
            t_scan = tcp_scan( get_ip_address(SPOOFED_NETWORK) ,get_ip_address(choice(SCAN_NETWORK)), int(choice(SCAN_PORT)))       
            t_scan.start()
        await asyncio.sleep(duration)


# Process msg. 
async def process_msg(msg):   
    global SCAN_NETWORK
    global SCAN_PORT
    global SCAN_RATE

    try:
        msg = json.loads(msg)
    except:
        print("Invalid data")
        return
    if not 'event' in msg.keys():
        print("Event not in the message.")
        return

    event = msg['event']
    payload = msg['data']

    if event == "EVT_SETUP":
        SCAN_NETWORK = payload['ip'].split(",")
        SCAN_RATE = int(payload['frequency'])
        SCAN_PORT = payload['port'].split(",")

    elif event == "EVT_INIT":
    
        SCAN_NETWORK = payload['ip'].split(",")
        SCAN_RATE = int(payload['frequency'])
        SCAN_PORT = payload['port'].split(",")
      
        print('[D] Starting Scan.')
        asyncio.ensure_future(scan())

    else:
        print("Unknown event {} received.".format(event))

# Receiver events.
async def recv_event():
    global COMM_HANDLE

    try:
        while (True):
            msg = await COMM_HANDLE.recv()
            print("[D] Received msg {}".format(msg))
            await process_msg(msg)

    except ConnectionRefusedError :
        print("[E] Unable to connect to Master")

    except websockets.exceptions.ConnectionClosed:
        print("[E] Master closed connection")

    COMM_HANDLE = None

    asyncio.ensure_future(comm_connect())

# Send event.
async def send_event(event, data):

    global MODULE, COMM_HANDLE

    if not COMM_HANDLE :
        print("[E] Controller not connected. Discarding")
        return

    msg = {}
    msg['timestamp'] = time.time()
    msg['event'] = event
    msg['device'] = MODULE
    msg['data'] = data

    msg = json.dumps(msg)

    print("Sending event")

    await COMM_HANDLE.send(msg)

# Connect event.
async def comm_connect():
    global COMM_HANDLE, MY_ADDR

    try:
        COMM_HANDLE = await websockets.connect('ws://{}:{}/{}'.format(MOD_IP, MOD_PORT, MODULE))
        MY_ADDR = COMM_HANDLE.local_address[0]
        print("[D] Connected to Master. My address is {}".format(MY_ADDR))
        asyncio.ensure_future(recv_event())
       
    except:
        COMM_HANDLE = None
        await asyncio.sleep(2)
        asyncio.ensure_future(comm_connect())


EVENT_LOOP = asyncio.get_event_loop()
asyncio.ensure_future(comm_connect())

print('[D] Starting scanner {} with {}:{}'.format(MODULE, MOD_IP, MOD_PORT))

try:
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    EVENT_LOOP.close()
