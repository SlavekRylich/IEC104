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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pass
    
    def run_server(self):
        self.socket.bind((self.ip,self.port))
        self.socket.listen(LISTENER_LIMIT)
        logging.info(f"Server listening on {self.ip}:{self.port}")
    
        
    def __enter__():
        
        pass
        
    def __exit__(*exc_info):
        pass