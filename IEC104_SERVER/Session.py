import socket
from CommModul import CommModule
import logging

LISTENER_LIMIT=5
# Konfigurace logování
logging.basicConfig(
    filename='server_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# # Příklad logování
# logging.info('Server starting...')
# logging.debug('Debugging information')
# logging.warning('Warning message')
# logging.error('Error occurred')
# logging.critical('Critical error')

# # Pro uzavření logovacího souboru
# logging.shutdown()

class Session():
    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        pass
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip,self.port))
        logging.info(f"Connected to {self.ip}:{self.port}")
        return self.socket


    def start_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip,self.port))
        self.socket.listen(LISTENER_LIMIT)
        logging.info(f"Server listening on {self.ip}:{self.port}")

    def disconnect(self):
        logging.info(f"Disconnecting")
        self.socket.close()

    async def start_server_async(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip,self.port))
        self.socket.listen(LISTENER_LIMIT)
        logging.info(f"Server listening on {self.ip}:{self.port}")

    async def connect_async(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        await self.socket.connect((self.ip,self.port))
        logging.info(f"Connected to {self.ip}:{self.port}")
        return self.socket

    def disconnect(self):
        logging.info(f"Server stopped")
        self.socket.close()
    
        
    def __enter__():
        
        pass
        
    def __exit__(*exc_info):
        pass