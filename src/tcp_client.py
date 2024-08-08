# TCP client
import socket
import time
import sys
import random
from loguru import logger as logging

logging.remove()
logging.add(sys.stdout, colorize=True, format="<level>{level.icon}</level> <level>{message}</level>", level="TRACE")


# logging.level(name='TRACE', icon='>', color='<magenta><bold>')
logging.level(name='INFO', icon='[~]', color='<cyan><bold>')
logging.level(name='WARNING', icon='[!]', color='<yellow><bold>')
logging.level(name='DEBUG', icon='[*]', color='<blue><bold>')
logging.level(name='ERROR', icon='[X]', color='<red><bold>')
logging.level(name='SUCCESS', icon='[#]', color='<green><bold>')

port = 10000
address = '198.7.0.2'
server_address = (address, port)

# function to generate a random string
def generate_string():
    length = random.randint(5, 10)
    r_string = ""
    for i in range (length):
        r_string += chr(random.randint(64, 123))
    return r_string


while True:
    time.sleep(1) # simulating a slower connection time
    try:
        logging.info(f"Connecting to {server_address}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.connect(server_address)
            logging.info(f'Handshake with {str(server_address)}')
        except:
            logging.error("Connection failed! Retrying in 1 second.")
            sock.close()
            continue
        
        # sending 3 messages
        for i in range(3):
            time.sleep(2) # simulating a time-consuming task

            message = generate_string()
            try:
                sock.send(message.encode('utf-8'))
                logging.info(f'Message sent: "{message}"')
                
                data = sock.recv(1024)
                if not data:
                    raise Exception("Connection ended!")
                
                logging.info(f'Message received: "{data}"')
            except Exception as e:
                logging.error(e)
                break
        sock.close()
        
    except KeyboardInterrupt:
        logging.warning("Exiting...")
        sys.exit(0)


