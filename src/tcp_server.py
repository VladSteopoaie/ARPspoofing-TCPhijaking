# TCP Server
import socket
import sys
from loguru import logger as logging

logging.remove()
logging.add(sys.stdout, colorize=True, format="<level>{level.icon}</level> <level>{message}</level>", level="TRACE")


# logging.level(name='TRACE', icon='>', color='<magenta><bold>')
logging.level(name='INFO', icon='[~]', color='<cyan><bold>')
logging.level(name='WARNING', icon='[!]', color='<yellow><bold>')
logging.level(name='DEBUG', icon='[*]', color='<blue><bold>')
logging.level(name='ERROR', icon='[X]', color='<red><bold>')
logging.level(name='SUCCESS', icon='[#]', color='<green><bold>')

# socket and socket options
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 10000
addr = '198.7.0.2'
server_address = (addr, port)
sock.bind(server_address)
logging.info(f"Server listening on {addr}:{port}")
sock.listen(5)

try:
    while True:
        logging.info('Waiting for connections...')
        conn, address = sock.accept()
        logging.info(f"Handshake with {address}")

        try:
            while True:
                data = conn.recv(1024)
                
                if not data:
                    raise Exception("Connection closed")
                
                logging.info(f'Message received: "{data}"')
                message = data + b'-server' # just append something to the data received and send it back
                conn.send(message)
                logging.info(f'Message sent: "{message}"')
        
        except Exception as e:
            logging.error(e)
            conn.close()
except Exception as e:
    logging.error(f"An error occured: {e}")
    sock.close()
