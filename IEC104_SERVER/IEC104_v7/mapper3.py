import json
import requests


class IEC101Mapper:
    def __init__(self):

        config_file = "mapper3.json"
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.global_config = self.config["global"][0]
        self.host = self.global_config["host"]
        self.port = self.global_config["port"]
        self.username = self.global_config["username"]
        self.password = self.global_config["password"]
        self.ASDU_address = self.global_config["ASDU_address"]
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
            return None
