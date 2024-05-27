# Project - IEC-104 

This project primally for my bachelor thesis. 
This is implementation of protocol IEC-104 for [Unipi Patron](https://kb.unipi.technology/en:hw:007-patron) series devices. 

## Requirements
Python >= 3.9
```bash
aiomqtt==2.1.0
asyncio==3.4.3
requests==2.31.0
```
 

## Installation

1. Update and upgrade your package repository.
```bash
sudo apt update && sudo apt upgrade
``` 

2. Install python3.
```bash
sudo apt install python3
```

3. Install pip package manager.
```bash
sudo apt install python3-pip -y
```

4. Create virtual enviroment for your project.
```bash
python3 -m venv venv
source venv/bin/activate
```

5. Use the package manager [pip](https://pip.pypa.io/en/stable/).
```bash
pip install -r requirements.txt
```

## Configuration
In config_parameters.json setup your IP address and MQTT configuration.
```json
{
    "server": {
        "ip_address": "192.168.1.10",
        "port": 2404,
        "k": 12,     
        "w": 8,
        "t0": 30,
        "t1": 15,
        "t2": 10,
        "t3": 20
    },
    "mqtt": {
        "enabled": true,
        "mqtt_broker_ip": "192.168.1.10",
        "mqtt_broker_port": 1883,
        "mqtt_username": "mqtt",
        "mqtt_password": "MQTTpass123",
        "mqtt_qos": 1
    }
}
```

In mapping_io.json setup your IOA address to correct pin. 
```json
{ "evok_conf": [
  {
    "host": "192.168.1.10",
    "port": 8080,
    "ASDU_address": 1
  }
],
  "mappings": [
    {
      "ioa": 1,
      "pin": "ai",
      "pin_id": "2_02",
      "command_method": "evok_api",
    },
    {
      "ioa": 2,
      "pin": "do",
      "pin_id": "1_01",
      "command_method": "evok_api",
    },
    {
      "ioa": 3,
      "pin": "ao",
      "pin_id": "1_01",
      "command_method": "gpio",
    },
    {
      "ioa": 4,
      "pin": "di",
      "pin_id": "1_01",
      "command_method": "gpio",
    }
  ]
}
```


## Usage
In bachelor project run server on RTU with:
```bash
python3 main_server.py
```

In bachelor project run client on MTU with:
```bash
python3 main_client_app.py
```

For use only IEC-104 communication, start server and register callbacks.
```python
import asyncio

from server import ServerIEC104


def on_connect(host, port, rc):
    pass

async def on_message(session, apdu, data, cb_on_sent):
    pass

def on_disconnect(session):
    pass

async def main(server):
    my_server = ServerIEC104()
    my_server.register_callback_on_connect = on_connect
    my_server.register_callback_on_message = on_message
    my_server.register_callback_on_disconnect = on_disconnect
    
    task_server = asyncio.create_task(my_server.start())
    
    # your code ...
    
    await task_server

if __name__ == "__main__":
    asyncio.run(main())

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## License

[Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)