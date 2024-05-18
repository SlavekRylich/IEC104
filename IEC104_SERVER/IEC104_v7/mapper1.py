import json
import requests

import ASDU


class IEC101Mapper:
    def __init__(self):

        config_file = "mapper1.json"
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.global_config = self.config["global"][0]
        self.host = self.global_config["host"]
        self.port = self.global_config["port"]
        self.username = self.global_config["username"]
        self.password = self.global_config["password"]
        self.ASDU_addr = self.global_config["ASDU_address"]
        # self.mappings = self.config["mappings"]
        self.iec101_type_mapping = {}
        for ioa in self.config["mappings_IEC101"].items():
            if ioa == "1":
                self.iec101_type_mapping[ioa] = self.handle_13()
            elif ioa == "2":
                self.iec101_type_mapping[ioa] = self.handle_45()
            elif ioa == "3":
                self.iec101_type_mapping[ioa] = self.handle_102()
            else:
                raise ValueError(f"Neznámý typ mapování: {ioa}")

        self.mappings_IO = {}
        for pin, pin_number, details in self.config["mappings_IO"].items():
            if pin == "di":
                self.mappings_IO[pin] = self.handle_di
            elif pin == "do":
                self.mappings_IO[pin] = self.handle_do
            else:
                raise ValueError(f"Neznámý typ mapování: {pin}")

    def handle_command(self, o_data, callback):
        print(type(o_data))
        type_id = str(o_data.type_id)
        if type_id in self.iec101_type_mapping:
            self.iec101_type_mapping[type_id](o_data, callback)
        else:
            print(f"Neznámý typ povelu IEC 104: {type_id}")


    def handle_gpio_mapping(self, mapping_details):
        pin = mapping_details["pin"]
        value_field = mapping_details.get("value_field", "value")

        def mapping_function(data):
            value = data[value_field]
            # Nastavení výstupu GPIO Raspberry Pi
            # Implementace záleží na konkrétní knihovně GPIO
            pass

        return mapping_function

    def handle_evok_request_mapping(self, mapping_details):
        iec101_type_mapping = {}
        for details in self.config["mappings"]["evok_api"]:
            if details["iec101_type_id"] == mapping_details.type_id:
                iec101_type_mapping[details] = self.handle_evok_request_mapping(mapping_details)
            elif details == "gpio":
                iec101_type_mapping[details] = self.handle_gpio_mapping(mapping_details)
            else:
                raise ValueError(f"Neznámý typ mapování: {mapping_details['type']}")
        dev_type = mapping_details["dev_type"]
        circuit = mapping_details["circuit"]
        value = mapping_details.get("value", "value")

        value_field = mapping_details.get("value_field", "value")

        def mapping_function(data):
            obj = data[1]
    def handle_iec101_message(self, iec101_message, callback):
        # Extrahování relevantních informací z IEC 101 zprávy
        asdu_address = iec101_message["asdu_address"]

        if self.ASDU_addr == asdu_address:

            information_object_address = iec101_message["information_object_address"]
            iec101_type_id = iec101_message["iec101_type_id"]
            value = iec101_message.get("value")

            # Vyhledání mapování pro danou ASDU adresu a informační objekt
            mapping = None
            for m in self.mappings_IO:
                if m["asdu_address"] == asdu_address and m["information_object_address"] == information_object_address:
                    mapping = m
                    break

            if mapping:
                # Vytvoření URL adresy pro REST API
                url = f"http://{self.global_config['host']}:{self.global_config['port']}/api/{mapping['command_method']}/{mapping['pin_id']}"

                # Vytvoření requestu pro REST API
                request_data = {
                    "value": value if value is not None else mapping.get("value")
                }

                # Odeslání requestu a zpracování odpovědi
                response = requests.post(url, json=request_data,
                                         auth=(self.global_config["username"], self.global_config["password"]))

                if response.status_code == 200:
                    # Zavolání callbacku s úspěšnou odpovědí
                    callback(response.json())
                else:
                    print(f"Chyba při odeslání requestu REST API: {response.status_code}")

    def handle_13(self, data):

        return 0

    def handle_45(self, data):

        return 0

    def handle_102(self, data):

        return 0

    def handle_di(self, details):
        pin_attr = details[""]
        pass

    def handle_do(self, details):
        pass
