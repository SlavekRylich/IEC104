import json

class ConfigLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.file_path, 'r') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            print(f"Config file '{self.file_path}' not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON in config file '{self.file_path}'.")
            return None

# Usage example
if __name__ == "__main__":
    config_loader = ConfigLoader('config_parameters.json')

    if config_loader.config:
        # load server config
        server_ip = config_loader.config['server']['ip_address']
        server_port = config_loader.config['server']['port']
        
        # load client config
        client_ip = config_loader.config['client']['ip_address']
        client_port = config_loader.config['client']['port']

        print(f"Server IP: {server_ip}, Port: {server_port}")
        print(f"Client IP: {client_ip}, Port: {client_port}")
