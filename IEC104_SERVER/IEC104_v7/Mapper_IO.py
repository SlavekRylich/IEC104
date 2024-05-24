import json
import requests


class IEC101Mapper:
    def __init__(self):

        config_file = "Mapper_IO.json"
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.evok_config = self.config["evok_conf"][0]
        self.host = self.evok_config["host"]
        self.port = self.evok_config["port"]
        self.username = self.evok_config["username"]
        self.password = self.evok_config["password"]
        self.ASDU_address = self.evok_config["ASDU_address"]
        self.mappings = self.config["mappings"]

    def handle_iec101_message(self, iec101_asdu_ioa):
        # Vyhledání mapování pro danou ASDU adresu a informační objekt
        mapping = None
        for m in self.mappings:
            if m["ioa"] == iec101_asdu_ioa:
                mapping = m
                break

        if mapping:
            return mapping
        else:
            print("Neznámé ioa v konfiguračním souboru.")
            return None
