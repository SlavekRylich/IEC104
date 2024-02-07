import socket
import pickle
import acpi
import time
import struct
import Frame

class CommModule:
    def __init__(self, sock):
        self.sock = sock
        self.connected = False
        self.frame = Frame.Frame()
    
    
    
    ## ********* GENERAL ********* ##
    
    def send_data(self, data):
        print(f"odeslány data: {data}")
        return self.sock.sendall(data)
    
    def receive_length(self, length=acpi.ACPI_HEADER_LENGTH):
        print(f"Receive {length} bytes.")
        return self.sock.recv(length)

    def receive_data(self):
        packed_header = None
        # Přijměte první dva byty pro získání délky rámce
        try:
            packed_header = self.sock.recv(acpi.ACPI_HEADER_LENGTH)
        except ConnectionAbortedError:
            # Spojení bylo ukončeno ze strany hostitelského počítače
            print("Spojení bylo ukončeno ze strany hostitelského počítače.")
        except socket.error as e:
            # Další možné chyby související se sokety
            print(f"Chyba při přijímání dat: {e}")
        
        if not packed_header:
            print("Při uzavření spojení nebo chybě vrátíme None")
            return None  # Při uzavření spojení nebo chybě vrátíme None
        
        unpacked_header = struct.unpack(f"{'B' * acpi.ACPI_HEADER_LENGTH}", packed_header)        
        header = unpacked_header
        print(f"prijata hlavicka: {header}")
        APDU_length = header[1]
        
        # pokud neobsahuje data
        if not (APDU_length - acpi.ACPI_HEADER_LENGTH):        
            return header, None
        
        # Přijetí zbytku rámce na základě délky uvedené v hlavičce
        packet_data = self.sock.recv(APDU_length)
        print("prajato dat", packet_data)
        
        data = self.frame.unpack_data(packet_data, APDU_length)
        
        return header, data
    
    def send_start_act(self):
        data = self.frame.pack(acpi.STARTDT_ACT)
        self.send_data(data)
        print("Odeslán start act.")
        
    def send_start_con(self):
        data = self.frame.pack(acpi.STARTDT_CON)
        print("Odeslán start con.")
        
        #
    def receive_start_act(self):
        data = self.frame.unpack_header(self.receive_data())
        if data[2] == acpi.STARTDT_ACT:
            print("Pokus o navázání spojení.")
        else:
            print("Chyba komunikace.")
            
    def receive_start_con(self):
        data = self.frame.unpack_header(self.receive_data())
        print(data)
        if data[2] == acpi.STARTDT_CON:
            self.connected = True
            print("Spojení úspěšně navázáno.")
        else:
            print("Chyba spojení.")
    
    ## Start sequence
    def send_startdt_sequence(self):
        # send Startdt ACT frame
        self.send_data(acpi.STARTDT_ACT)
        print("Odeslán startdt act.")
        
        # 
        data = self.receive_data()
        if data == acpi.STARTDT_CON:
            self.connected = True
            print("Spojení úspěšně navázáno.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
        
    ## Stop sequence
    def send_stopdt_sequence(self):
        # send Stopdt ACT frame
        self.send_data(acpi.STOPDT_ACT)
        print("Odeslán stopdt act.")
        
        # 
        data = self.receive_data()
        if data == acpi.STOPDT_CON:
            self.connected = False
            print("Spojení úspěšně ukončeno.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
    
    ## TESTFR sequence
    def send_testfr_sequence(self):
        # send Start ACT frame
        self.send_data(acpi.TESTFR_ACT)
        print("Odeslán testfr act.")
        
        # 
        data = self.receive_data()
        print(data)
        if data == acpi.TESTFR_CON:
            self.connected = True
            print("Úspěšně přijat testfr con. Otestováno.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
        
    ## Response startdt sequence
    def resp_startdt_sequence(self):
        data = self.receive_data()
        if data == acpi.STARTDT_ACT:
            self.send_data(acpi.STARTDT_CON)
            print("Přijato startdt act, odesláno startdt con.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
        
    ## Response stopdt sequence
    def resp_stopdt_sequence(self):
        data = self.receive_data()
        if data == acpi.STOPDT_ACT:
            self.send_data(acpi.STOPDT_CON)
            print("Přijato stopdt act, odesláno stopdt con.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
        
    ## Response testfr sequence
    def resp_testfr_sequence(self):
        data = self.receive_data()
        if data == acpi.TESTFR_ACT:
            self.send_data(acpi.TESTFR_CON)
            print("Přijato testfr act, odesláno testfr con.")
            return 1
        else:
            print("Chyba spojení.")
            return 0
            
    def connection_timeout(self, socket):
        #time.sleep(acpi.T0)
        if not self.connected:
            print("Chyba: Časový limit pro připojení vypršel.")
            self.sock.close()
            
    
        
    ## ********* CLIENT ********* ##
    
    ## ********* SERVER ********* ##
    
