from abc import ABC, abstractmethod

class MqttInterface(ABC):
    @abstractmethod
    def connect(self, host, port, username, password):
        # """Pøipojení k MQTT brokeru."""
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
        # """Pøihlášení k odbìru z topicu a nastavení funkce pro zpracování zpráv."""
        pass

    from paho.mqtt.client import Client

    class IMqttProtokol:
        def __init__(self, client_id: str, broker_url: str, port: int, username: str = None, password: str = None):
            """
            Inicializace klienta MQTT.

            Args:
                client_id: Identifikátor klienta.
                broker_url: URL adresa brokera.
                port: Port brokera.
                username: Uživatelské jméno pro autentizaci (volitelnì).
                password: Heslo pro autentizaci (volitelnì).
            """
            self._client = Client(client_id)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            self._broker_url = broker_url
            self._port = port
            self._username = username
            self._password = password

        def _on_connect(self, client, userdata, flags, rc):
            """
            Metoda volaná po pøipojení klienta k brokerovi.

            Args:
                client: Klient MQTT.
                userdata: Uživatelská data (nepoužíváno).
                flags: Pøíznaky pøipojení.
                rc: Kód návratu pøipojení.
            """
            raise NotImplementedError

        def _on_message(self, client, userdata, message):
            """
            Metoda volaná po pøijetí zprávy klientem.

            Args:
                client: Klient MQTT.
                userdata: Uživatelská data (nepoužíváno).
                message: Zpráva MQTT.
            """
            raise NotImplementedError

        def _on_disconnect(self, client, userdata, rc):
            """
            Metoda volaná po odpojení klienta od brokera.

            Args:
                client: Klient MQTT.
                userdata: Uživatelská data (nepoužíváno).
                rc: Kód návratu odpojení.
            """
            raise NotImplementedError

        def pripojit(self):
            """
            Pøipojení klienta k brokerovi.
            """
            raise NotImplementedError

        def odpojit(self):
            """
            Odpojení klienta od brokera.
            """
            raise NotImplementedError

        def publikovat(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False):
            """
            Publikování zprávy na zadané téma.

            Args:
                topic: Téma zprávy.
                payload: Data zprávy.
                qos: Úroveò kvality služby (0, 1, 2).
                retain: True pro uchování zprávy na brokerovi i po odpojení klienta.
            """
            raise NotImplementedError

        def prihlasit_se(self):
            """
            Pøihlášení klienta k brokerovi s uživatelským jménem a heslem (pokud jsou definovány).
            """
            raise NotImplementedError

        def odhlasit_se(self):
            """
            Odhlášení klienta od brokera.
            """
            raise NotImplementedError

