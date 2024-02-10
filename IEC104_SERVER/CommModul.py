import socket
import acpi
import struct
from Iformat import IFormat
from Sformat import SFormat
from Uformat import UFormat



class CommModule:
    def __init__(self, sock):
        self.sock = sock
        self.connected = False
        self.buffer_all_frames = []
        self.buffer_I_frames = []
        self.buffer_S_frames = []
        self.buffer_U_frames = []
    
    
    
    
    ## ********* GENERAL ********* ##
    
    def send_data(self, data):
        print(f"odeslány data: {data}")
        return self.sock.sendall(data)
    
    def receive_length(self):
        receive_packet = self.sock.recv(2)
        
        # pokud se vubec jedna o iec104 paket
        if receive_packet[0] == 0x68:
            
            # prijeti zbytku paketu dle délky v hlavičce
            apdu=self.sock.recv(receive_packet[1]) 
            acpi_header = apdu[:(acpi.ACPI_HEADER_LENGTH - 1)]
            
            frame_format = self.what_format(acpi_header)
            
            if frame_format == "I":
                
                ssn = (acpi_header[1] << 7) + (acpi_header[0] >> 1) 
                rsn = (acpi_header[3] << 7) + (acpi_header[2] >> 1)
                asdu_data = apdu[acpi.ACPI_HEADER_LENGTH:]
                
                # vytvoreni nove instance Iformatu a vlozeni do bufferu
                new_instance = IFormat(asdu_data, ssn, rsn)
                self.buffer_I_frames.append(new_instance)
                self.buffer_all_frames.append(new_instance)
                
                return asdu_data
                
            elif frame_format == "S":
                
                rsn = (acpi_header[3] << 7) + (acpi_header[2] >> 1)
                
                new_instance = SFormat(rsn)
                self.buffer_S_frames.append(new_instance)
                self.buffer_all_frames.append(new_instance)
                
                # logika potvrzování přijatých dat
                pass
            
                # kód označující že byl proveden U format
                return 1
                
            elif frame_format == "U":
                first_byte = acpi_header[0]
                
                new_instance = UFormat()
                
                # STARTDT ACT
                if first_byte == acpi.STARTDT_ACT:
                    new_instance.structure(acpi.STARTDT_ACT)
                    
                    self.buffer_U_frames.append(new_instance)
                    self.buffer_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.structure(acpi.STARTDT_CON)
                    
                    self.send_data(new_instance.structure())
                    print("prijato startdt act, posilam startdt con")
                    
                    self.active_session = True
                    
                # STOPDT ACT
                elif first_byte == acpi.STOPDT_ACT:
                    new_instance.structure(acpi.STOPDT_ACT)
                    
                    self.buffer_U_frames.append(new_instance)
                    self.buffer_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.structure(acpi.STOPDT_CON)
                    
                    self.send_data(new_instance.structure())
                    
                    print("prijato stopdt act, posilam stopdt con a přenos je ukončen")
                    self.active_session = False
                
                # TESTDT ACT
                elif first_byte == acpi.TESTFR_ACT:
                    new_instance.structure(acpi.TESTFR_ACT)
                    
                    self.buffer_U_frames.append(new_instance)
                    self.buffer_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.structure(acpi.TESTFR_CON)
                    
                    self.send_data(new_instance.structure())
                    print("prijato testdt act, odeslano testdt. spojeni je aktivní")
                     
                # kód označující že byl proveden U format           
                return 0
            
            else:
                raise Exception("Přijat neznámí formát")
            
            
        return ''

    
    def what_format(self, first_byte):
        first_byte = first_byte[0]
        if not (first_byte & 1):
            print(f"I format {first_byte & 0xFF}")
            return "I"
        elif (first_byte & 3) == 1:
            print(f"S format {first_byte & 0xFF}")
            return "S"
        elif (first_byte & 3) == 3: 
            print(f"U format {first_byte & 0xFF}")
            return "U"
        else:
            print("Nejaky zpičený format")
            return None
        
        
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
    
