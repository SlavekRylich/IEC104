import json
import struct
import requests


class IEC101_REST_MAP:
    def __init__(self):
        config_file = "Mapper.json"
        with open(config_file, "r") as f:
            self.config = json.load(f)
        self.host = self.config["host"]
        self.mapping = {}
        for command_type, mapping_details in self.config["mappings"].items():
            if mapping_details["type"] == "gpio":
                self.mapping[command_type] = self.handle_gpio_mapping(mapping_details)
            elif mapping_details["type"] == "analog_input":
                self.mapping[command_type] = self.handle_analog_input_mapping(mapping_details)
            elif mapping_details["type"] == "evok_request":
                self.mapping[command_type] = self.handle_evok_request_mapping(mapping_details)
            else:
                raise ValueError(f"Neznámý typ mapování: {mapping_details['type']}")

    def handle_command(self, data):
        print(type(data))
        command_type = str(data[0])
        if command_type in self.mapping:
            self.mapping[command_type](data)
        else:
            print(f"Neznámý typ povelu IEC 104: {command_type}")

    def handle_gpio_mapping(self, mapping_details):
        pin = mapping_details["pin"]
        value_field = mapping_details.get("value_field", "value")

        def mapping_function(data):
            value = data[value_field]
            # Nastavení výstupu GPIO Raspberry Pi
            # Implementace záleží na konkrétní knihovně GPIO
            pass

        return mapping_function

    def handle_analog_input_mapping(self, mapping_details):
        channel = mapping_details["channel"]
        value_field = mapping_details.get("value_field", "value")

        def mapping_function(data):
            value = data[value_field]
            # Čtení analogového vstupu Raspberry Pi
            # Implementace záleží na konkrétní knihovně ADC
            pass

        return mapping_function

    def handle_evok_request_mapping(self, mapping_details):
        dev_type = mapping_details["dev_type"]
        circuit = mapping_details["circuit"]
        value = mapping_details.get("value", "value")

        value_field = mapping_details.get("value_field", "value")

        def mapping_function(data):
            obj = data[1]
            value = data[value_field]
            # Odeslání REST API requestu pro modul Evok
            # Implementace záleží na konkrétní knihovně pro HTTP requesty

            def get_request(host: str, dev_type: str, circuit: str):
                url = f"http://{self.host}/rest/{dev_type}/{circuit}"
                return requests.get(url=url)

            if __name__ == '__main__':
                ret = get_request(host='127.0.0.1', dev_type='di', circuit='1_01')
                print(ret.json())

            def send_request(host: str, dev_type: str, circuit: str, value: bool):
                url = f"http://{host}/rest/{dev_type}/{circuit}"
                data = {'value': str(int(value))}
                return requests.post(url=url, data=data)

            if __name__ == '__main__':
                ret = send_request(host='127.0.0.1', dev_type='do', circuit='1_01', value=True)
                print(ret.json())
            pass

        return mapping_function

if __name__ == "__main__":
    # Příklad použití
    iec104_mapper = IEC101_REST_MAP()

    # Simulace příjmu dat z protokolu IEC 104
    data = struct.pack(">BBI", 101, 1, 0)  # M_SP_NA_1: Číst analogovou hodnotu z IOA 1
    iec104_mapper.handle_command(data)

    data = struct.pack(">BBI", "C_SC_NA_1", 1, 0)  # M_SP_NA_1: Číst analogovou hodnotu z IOA 1
    iec104_mapper.handle_command(data)

    data = struct.pack(">BBI", 102, 1, 3.14)  # C_SP_NA_1: Nastavit analogovou hodnotu na IOA 1 na 3.14
    iec104_mapper.handle_command(data)

    data = struct.pack(">BBI", 103, 1, 1)  # C_ACT_CONT: Zapnout výstup DOA 1
    iec104_mapper.handle_command(data)

    data = struct.pack(">BBI", 104, 1, 0)  # I_SP_NA_1: Potvrdit příjem povelu pro IOA 1
    iec104_mapper.handle_command(data)
