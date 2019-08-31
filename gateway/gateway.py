import asyncio
import websockets
import json
import time
import os
from scapy.config import conf
from scapy.all import sniff, Ether, ARP, srp, conf 
from scapy.data import ETH_P_ALL
import logging
import sys
import signal
from uuid import getnode as get_mac
import subprocess
import signal
signal.signal(signal.SIGHUP, signal.SIG_IGN)

# Constants
MOD_PORT = 12001
MOD_IP = "172.16.131.64"
MODULE = 'gateway' 
INTERFACE = "ens4"
SLEEP_DURATION = 20
IOT_DEVICE_DICT = {}
GROUND_TRUTH_FILE = ''
FIM_TABLE_SIZE = 1000
SAFE_PORTS = ['67', '68', '53', '123']

# Variables
logging.basicConfig(level=logging.INFO, filename='/var/log/'+MODULE+'.log', filemode='a', format='%(name)s - %(asctime)s - %(levelname)s  - %(message)s')
GROUND_TRUTH = []
COMM_HANDLE = None
flow_queue = asyncio.Queue()

try:
    MOD_IP = sys.argv[1]
    INTERFACE = sys.argv[2]
    IOT_SUBNET = sys.argv[3]
    GW_ID = sys.argv[4]
except:
    logging.error('mod_ip/interface/iot_subnet/gw_id not configured. Exiting.')
    sys.exit('Exiting.')

MODULE += GW_ID
logging.info('Interface: {}, Manager: {}, Subnet:{}'.format(INTERFACE, MOD_IP, IOT_SUBNET))

# arp scan for available IoT devices.
def find_iot_devices(i_network):
    global IOT_DEVICE_DICT
    conf.iface=INTERFACE
    bdcast = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=i_network)
    ans, uans = srp(bdcast, timeout=2, verbose=False)
    for i in ans:
        IOT_DEVICE_DICT[i[1]['ARP'].hwsrc] = i[1]['ARP'].psrc

    logging.info('Found these IoT devices: {}'.format(IOT_DEVICE_DICT))
    asyncio.ensure_future(send_event('EVT_GW_DEVICES', list(IOT_DEVICE_DICT.values())))

# To manage the stored entries.
class storage_handler(object):
    def __init__(self):
        self._fim_table_max_size = FIM_TABLE_SIZE
        self._fim_table = {} 

    def _is_fim_table_full(self):
        if len(self._fim_table) ==  self._fim_table_max_size:
            return True
        return False

    def get_fim_entries(self):
        return self._fim_table.copy()

    def insert_fim(self, i_key : str, i_val : dict):
        
        if not self._is_fim_table_full():
            try:
                l_ret = self._lookup_fim(i_key)

                if not l_ret is None:

                    for k1 in l_ret.keys(): 
                        for k2 in i_val.keys(): 
                            if k1 == k2 and not k1 == 'time':
                                l_ret[k1] += i_val[k2] 
                    
                    self._fim_table[i_key] = l_ret
                
                else:
                    logging.debug('Added :{}'.format(i_key))
                    self._fim_table[i_key] = i_val
            except:
                logging.error('Exception insert_fim.')
        else:
            logging.debug('FIM table is full.')
            raise Exception('FIM Table filled.')


    def delete_fim(self, i_key):
        try:
            del self._fim_table[i_key]
        except:
            pass

    def _empty_fim(self):
        self._fim_table.clear()

    def _lookup_fim(self, i_key):   
        try:    
            return self._fim_table[i_key]
        except:
            return None

# pkt processing
class packet_to_dict(object):
    def __init__(self, i_dev_mac_ip, i_safe_ports):
        self._del_entries = 100
        self._conn_table = {}
        self._dns_dict = {}
        self._conn_list = []
        self._safe_ports = i_safe_ports
        self._pkt = None
        self._device_mac_ip = i_dev_mac_ip

    def add(self, i_pkt):
        self._pkt = i_pkt
        if len(self._conn_table) ==  10*self._del_entries:
            logging.info('Clearing stale table entries.')
            try:
                for conn in self._conn_list[:-2*self._del_entries]:
                    self._conn_list.remove(conn)
                    del self._conn_table[conn]
            except:
                logging.error(sys.exc_info())
        return self._extract()

    def _check_dns(self):
        if self._pkt.haslayer('DNSRR') and (self._pkt['UDP'].sport == 53 or self._pkt['UDP'].dport == 53):
            for a_count in range(self._pkt['DNS'].ancount):
                try:
                    ip = self._pkt['DNSRR'][a_count].rdata
                    name = self._pkt['DNSRR'][a_count].rrname

                    if isinstance(ip, bytes):
                        ip = ip.decode()
                    if isinstance(name, bytes):
                        name = name.decode()                 

                    self._dns_dict[ip] = name

                except:
                	pass

    def _get_domain_name(self, ip):

        if ip in self._dns_dict.keys():
            while True:
                try:
                    domain_name = self._dns_dict[ip]
                    ip = domain_name
                except:
                    break
        return ip

    def _extract(self):
        spoof = False
        try: 
            smac = self._pkt['Ether'].src
            dmac = self._pkt['Ether'].dst

            src = self._pkt['IP'].src
            dst = self._pkt['IP'].dst
        except:
            logging.error(sys.exc_info())
            return None

        if src in self._device_mac_ip.values():
            direction = 0
        elif dst in self._device_mac_ip.values():
            direction = 1
        elif smac in self._device_mac_ip.keys():
            # If src/dst IP is not there but mac is, it means spoofing.
            direction = 0
            #logging.info('Spoof: {} {} {} {}'.format(smac, dmac, src,dst))
            spoof = True
        else:
            return None


        if (self._pkt['IP'].proto == 6 or self._pkt['IP'].proto == 17):
            if not spoof:
                self._check_dns()

            sip = self._get_domain_name(src)
            dip = self._get_domain_name(dst)
            proto = self._pkt['IP'].proto
            length = self._pkt['IP'].len
            time = self._pkt.time
            pflag = 0
            sflag = 0
            if proto == 6:
                sport = self._pkt['TCP'].sport
                dport = self._pkt['TCP'].dport
                if str(self._pkt['TCP'].flags).find('P') >=0:
                    pflag = 1

                if str(self._pkt['TCP'].flags) == 'S':
                    sflag = 1

            elif proto == 17:
                sport = self._pkt['UDP'].sport
                dport = self._pkt['UDP'].dport
            else:
                sport = 0
                dport = 0

            if spoof:
                key = sip+","+dip+","+str(proto)+","+str(dport)+","+str(direction)
                return {'key': key, 'values': {'sport': str(sport), 'insize': 0, 'outsize': length, 'incount': 0,\
                     'outcount': 1, 'pcount':pflag, 'scount':sflag, 'time':time}}

            temp_key_1 = sip+","+dip+","+str(proto)+","+str(sport)+","+str(dport)
            temp_key_2 = dip+","+sip+","+str(proto)+","+str(dport)+","+str(sport)

            temp_key = temp_key_1

            if temp_key_1 in self._conn_table.keys():
                key = self._conn_table[temp_key_1]['key']
                self._conn_list.remove(temp_key_1)
                self._conn_list.append(temp_key_1)
            elif temp_key_2 in self._conn_table.keys():
                key = self._conn_table[temp_key_2]['key']
                self._conn_list.remove(temp_key_2)
                self._conn_list.append(temp_key_2)
                temp_key = temp_key_2
            else:
                if direction == 0:
                    key = sip+","+dip+","+str(proto)+","+str(dport)+","+str(direction)
                else:
                    key = dip+","+sip+","+str(proto)+","+str(dport)+","+str(direction)
                self._conn_table[temp_key_1] = {'dir':direction, 'key':key}
                self._conn_list.append(temp_key_1)
            
            if direction == self._conn_table[temp_key]['dir']:
                sport = str(sport)
            else:
                sport = str(dport)

            if key.split(',')[3] in self._safe_ports:
                return None

            if direction == 0:
                return {'key': key, 'values': {'sport': sport, 'insize': 0, 'outsize': length, 'incount': 0,\
                     'outcount': 1, 'pcount':pflag, 'scount':sflag, 'time':time}}
            else:
                return {'key': key, 'values': {'sport': sport, 'outsize': 0, 'insize': length, 'incount': 1,\
                     'outcount': 0, 'pcount':pflag, 'scount':sflag, 'time':time}}
             
        else:
                return None


def send_fim_entries(i_input):
    if not i_input is None:
        
        if len(i_input) > 0:
            asyncio.ensure_future(send_event('EVT_CONN_ANOMALY', {'key_val' : i_input})) 


async def periodic_task():
    while True:
        await asyncio.sleep(SLEEP_DURATION)
        fim = store_handle.get_fim_entries()
        if(len(fim)>0):
            send_fim_entries(fim)
            store_handle._empty_fim() 


async def conn_task():
    while True:
        l_ret = await flow_queue.get()

        try:
            l_key = l_ret['key'] + ',' + l_ret['values']['sport']
            del l_ret['values']['sport']
            store_handle.insert_fim(l_key, l_ret['values'])
        except:
            logging.debug('Table filled. Sending entries.')
            fim = store_handle.get_fim_entries()
            send_fim_entries(fim)
            store_handle._empty_fim()


def set_ground_truth(i_data):
    global GROUND_TRUTH
    GROUND_TRUTH = i_data
    """
    try:
        ret_dict = {}
        df = pd.read_csv(i_file, header=0) 

        for _, row in df.iterrows(): 
            ret_dict[row['key']] = {'meanSize' : row['meanSize'], 'meanCount' : row['meanCount'], 'stdSize' : row['stdSize'], 'stdCount' : row['stdCount'] }
        return ret_dict
    except:
        logging.info('Alert---> Ground Truth file not set.')
        return {}

    logging.debug("Ground truth is {}".format(GROUND_TRUTH))
    """


def process_packet():
    l_pkt = SNIFF_SOCK.recv()

    l_ret = pkt_dict.add(l_pkt)

    if not  l_ret is None:
        #if not l_ret['key'] in GROUND_TRUTH.keys():
        ## Look for destinations.
        temp = l_ret['key'].split(',')
        if not temp[1] in GROUND_TRUTH:
            asyncio.ensure_future(flow_queue.put(l_ret))
        else:
            # add behavioral case
            pass


async def recv_event():
    global COMM_HANDLE

    try:
        while (True):
            msg = await COMM_HANDLE.recv()
            logging.debug("Received msg {}".format(msg))
            process_msg(msg)

    except ConnectionRefusedError :
        logging.debug("Unable to connect to Master")

    except websockets.exceptions.ConnectionClosed:
        logging.debug("Master closed connection")

    COMM_HANDLE = None

    asyncio.ensure_future(comm_connect())


async def send_event(event, data):
    global MODULE, COMM_HANDLE

    if not COMM_HANDLE is None:
        msg = {}
        msg['timestamp'] = time.time()
        msg['event'] = event
        msg['sender'] = MODULE
        msg['receiver'] = 'master'
        msg['data'] = data

        msg = json.dumps(msg)

        logging.debug("Sending event {}".format(msg))

        await COMM_HANDLE.send(msg)
    else:
        logging.debug('Master not connected.')

def process_msg(msg):
    try:
        msg = json.loads(msg)

        if 'event' not in msg or 'data' not in msg or 'sender' not in msg or 'receiver' not in msg:
            logging.error("Invalid json format. Key(s) missing.")
            return

    except:
        print("Invalid data")
        return

    event, data = (msg['event'], msg['data'])

    if event == "SET_GROUND_TRUTH":
        pass
    else:
        logging.error("Unknown event {} received.".format(event))


async def comm_connect():
    global COMM_HANDLE

    try:
        COMM_HANDLE = await websockets.connect('ws://{}:{}/{}'.format(MOD_IP, MOD_PORT, MODULE))
        logging.debug("Connected to Master")
        # This can be kept as seperate task and IoT devices can be discovered dynamically.
        find_iot_devices(IOT_SUBNET)
        asyncio.ensure_future(recv_event())
    except:
        COMM_HANDLE = None
        await asyncio.sleep(5)
        asyncio.ensure_future(comm_connect())

signal.signal(signal.SIGHUP, signal.SIG_IGN)

pkt_dict = packet_to_dict(IOT_DEVICE_DICT, SAFE_PORTS)
store_handle = storage_handler()

SNIFF_SOCK = conf.L2listen(type=ETH_P_ALL, iface=INTERFACE, filter='ip')

EVENT_LOOP = asyncio.get_event_loop()
EVENT_LOOP.add_reader(SNIFF_SOCK, process_packet)
asyncio.ensure_future(comm_connect())
asyncio.ensure_future(conn_task())
asyncio.ensure_future(periodic_task())

logging.debug("Listeing for packets on {}".format(INTERFACE))
try:
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    SNIFF_SOCK.close()
    logging.debug("!!!! Program ended !!!!")
