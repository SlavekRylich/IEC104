import socket
import Frame
import IFormat
import SFormat
import UFormat
import acpi
import struct



class CommModule:
    def __init__(self, socket):
        self.socket = socket
        #self.socket_addr = socket[1]
        
        
        self.connected = False
        self.buffer_recv_all_frames = []
        self.buffer_recv_I_frames = []
        self.buffer_recv_S_frames = []
        self.buffer_recv_U_frames = []
        
        self.buffer_send_all_frames = []
        self.buffer_send_I_frames = []
        self.buffer_send_S_frames = []
        self.buffer_send_U_frames = []
        
    ## pro řízení pomocí U formátu
    def send_U_format(self, type):
        request = type
        response_type = ''
        
        if request == acpi.STARTDT_ACT:
            response_type = acpi.STARTDT_CON
            
        elif request == acpi.STOPDT_ACT:
            response_type = acpi.STOPDT_CON
            
        elif request == acpi.TESTFR_ACT:
            response_type = acpi.TESTFR_CON
        else:
            print("neodeslalo se nic")
            return 1
        
        try:
            new_instance = UFormat()
            
            new_instance.set_structure(request)
            
            self.socket.sendall(new_instance.get_structure())
            
            self.buffer_send_U_frames.append(new_instance)
            self.buffer_send_all_frames.append(new_instance)
            
            
            response = self.socket.recv(2)
            
            # pokud se vubec jedna o iec104 paket
            if response[0] == 0x68:
                
                # prijeti zbytku paketu dle délky v hlavičce
                apdu = self.socket.recv(response[1]) 
                acpi_header = apdu[:(acpi.ACPI_HEADER_LENGTH - 1)]
                
                frame_format = self.what_format(acpi_header)
                
                if frame_format == "U":
                    first_byte = acpi_header[0]
                    
                    new_instance = UFormat()
                    
                    if first_byte == response_type:
                        new_instance.set_structure(response_type)
                        
                        self.buffer_recv_U_frames.append(new_instance)
                        self.buffer_recv_all_frames.append(new_instance)
                        
                        # uspěšně přijata odpověď ... con
                        return 0
                    
                # neni iec104 komunikace, nebyl to U format a nebylo to ... con
            return 1
            
        except Exception as e:
            print(f"Exception: {e}")
            
            return 1
    
    
    def send_data(self, data):
        print(f"odeslány data: {data}")
        
        new_instance = IFormat(data)
        
        self.buffer_send_I_frames.append(new_instance)
        self.buffer_send_all_frames.append(new_instance)
        
        return self.socket.sendall(new_instance.get_structure())
    
    def receive_traffic(self):
        
        while True:
        
            receive_packet = self.socket.recv(1)
        
            if not receive_packet:
                break
        
            buffer += receive_packet

            if len(buffer) >= 1 and buffer[0] != 0x68:
                print("Nepřijatý očekávaný start byte. Vyprázdnění bufferu.")
                buffer = b''
        
        
        receive_packet = self.socket.recv(2)
        
        if not receive_packet:
            return None
        
        receive_packet = struct.unpack(f"{'B' * 2}", receive_packet)
        
        # pokud se vubec jedna o iec104 paket
        if receive_packet[0] == 0x68:
            
            # prijeti zbytku paketu dle délky v hlavičce
            apdu = self.socket.recv(receive_packet[1]) 
            
            # rozbalení po bytech
            apdu = struct.unpack(f"{'B' * receive_packet[1]}", apdu)
            
            acpi_header = apdu[:(acpi.ACPI_HEADER_LENGTH - 1)]
            
            frame_format = self.what_format(acpi_header)
            
            if frame_format == "I":
                
                ssn = (acpi_header[1] << 7) + (acpi_header[0] >> 1) 
                rsn = (acpi_header[3] << 7) + (acpi_header[2] >> 1)
                asdu_data = apdu[acpi.ACPI_HEADER_LENGTH:]
                
                # vytvoreni nove instance Iformatu a vlozeni do bufferu
                new_instance = IFormat(asdu_data, ssn, rsn)
                self.buffer_recv_I_frames.append(new_instance)
                self.buffer_recv_all_frames.append(new_instance)
                
                return (0, new_instance)
                
            elif frame_format == "S":
                
                rsn = (acpi_header[3] << 7) + (acpi_header[2] >> 1)
                
                new_instance = SFormat(rsn)
                self.buffer_recv_S_frames.append(new_instance)
                self.buffer_recv_all_frames.append(new_instance)
                
                # logika potvrzování přijatých dat
                pass
            
                # kód označující že byl proveden S format
                return (1, new_instance)
                
            elif frame_format == "U":
                first_byte = acpi_header[0]
                
                new_instance = UFormat()
                
                # STARTDT ACT
                if first_byte == acpi.STARTDT_ACT:
                    new_instance.set_structure(acpi.STARTDT_ACT)
                    
                    self.buffer_recv_U_frames.append(new_instance)
                    self.buffer_recv_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.set_structure(acpi.STARTDT_CON)
                    
                    self.socket.sendall(new_instance.get_structure())
                    print("prijato startdt act, posilam startdt con")
                    
                    self.active_session = True
                    
                    return (2, new_instance)
                    
                # STOPDT ACT
                elif first_byte == acpi.STOPDT_ACT:
                    new_instance.set_structure(acpi.STOPDT_ACT)
                    
                    self.buffer_recv_U_frames.append(new_instance)
                    self.buffer_recv_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.set_structure(acpi.STOPDT_CON)
                    
                    self.socket.sendall(new_instance.get_structure())
                    
                    print("prijato stopdt act, posilam stopdt con a přenos je ukončen")
                    self.active_session = False
                    
                    return (3, new_instance)
                
                # TESTDT ACT
                elif first_byte == acpi.TESTFR_ACT:
                    new_instance.set_structure(acpi.TESTFR_ACT)
                    
                    self.buffer_recv_U_frames.append(new_instance)
                    self.buffer_recv_all_frames.append(new_instance)
                    
                    new_instance = UFormat()
                    new_instance.set_structure(acpi.TESTFR_CON)
                    
                    self.socket.sendall(new_instance.get_structure())
                    print("prijato testdt act, odeslano testdt. spojeni je aktivní")
                    
                    return (4, new_instance)
                
                else:
                    # nemělo by nikdy nastat           
                    return  5
            
            else:
                raise Exception("Přijat neznámí formát")
            
            
        return ''

    
    
        
        
    def receive_data(self):
        packed_header = None
        # Přijměte první dva byty pro získání délky rámce
        try:
            packed_header = self.socket.recv(acpi.ACPI_HEADER_LENGTH)
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
        packet_data = self.socket.recv(APDU_length)
        print("prajato dat", packet_data)
        
        data = self.frame.unpack_data(packet_data, APDU_length)
        
        return header, data
    
    def connection_timeout(self, socket):
        #time.sleep(acpi.T0)
        if not self.connected:
            print("Chyba: Časový limit pro připojení vypršel.")
            self.socket.close()
            
    
        
    ## ********* CLIENT ********* ##
    
    ## ********* SERVER ********* ##
    
