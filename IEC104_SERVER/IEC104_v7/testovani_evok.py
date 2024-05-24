import socket

# Nastavení cílového serveru a portu
host = "192.168.1.10"  # Změňte na adresu serveru, pokud je jiná
port = 2404  # Změňte na port serveru, pokud je jiný

# Vytvoření TCP socketu
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Připojení k serveru
s.connect((host, port))

# Zpráva, která se odešle
zprava = "Ahoj ze skriptu v Pythonu!"

# Odeslání zprávy
s.send(zprava.encode('utf-8'))

# Zavření socketu
s.close()

print("Zpráva odeslána na server", host, "na port", port)