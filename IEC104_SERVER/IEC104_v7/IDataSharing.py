# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class IDataSharing(ABC):
    @abstractmethod
    def connect(self, host, port, username, password):
        """Připojení k MQTT brokeru."""
        pass

    @abstractmethod
    def disconnect(self):
        """Odpojení od MQTT brokera."""
        pass

    @abstractmethod
    def publish(self, topic, message):
        """Odeslání zprávy do topicu."""
        pass

    @abstractmethod
    def subscribe(self, topic, callback):
        """Přihlášení k odběru z topicu a nastavení funkce pro zpracování zpráv."""
        pass

    @abstractmethod
    def save_data(self, topic, data, callback):
        """Ukládání dat do zprávy."""
        pass

    @abstractmethod
    def send_data(self, callback):
        """Odeslání zprávy."""
        pass
