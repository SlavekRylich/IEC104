# employee.py

from datetime import date

class Session():
    # třídní proměná pro uchování unikátní id každé instance
    id = 0
    instances = []
    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.connected = False
        self.active_transaction = False
        self.timeout = 0
        self.sessions = []
        
        Session.id += 1
        self.id = Session.id
        Session.instances.append(self)
        
        
    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
        if isinstance(id, int):
            if id < len(cls.instances):
                
                del cls.instances[id-1]
                return True
            else:
                return False
        else:
            if id: 
                    cls.instances.remove(id)
                    return True
            else:
                return False
    
    @classmethod
    def get_all_instances(cls):
        return cls.instances
    
    @classmethod
    def get_instance(cls, id):
        for inst in cls.instances:
            if inst.id == id:
                return inst
        return None

    def __str__(self) -> str:
        return (f"{self.ip}:{self.port}")
    
    def __del__(self):
        print(f"Instance {self.id} is destroyed!")
    

if __name__ == '__main__':
    list = []
    ips = [
        '127.0.0.1',
        '127.0.0.2',
        '127.0.0.3',
        '127.0.0.4',
        '127.0.0.5',
        '127.0.0.6',
        '127.0.0.7',
        '127.0.0.8',
        '127.0.0.9',
        '127.0.0.10'
    ]
    ports = ['3000',
            '3001',
            '3002',
            '3003',
            '3004',
            '3005',
            '3006',
            '3007',
            '3008',
            '3009'
    ]
    
    # vzorova instance
    session = Session('127.0.1.1', '1234')
    
    for i in range (0,9):
        list.append(Session(ips[i], ports[i]))
        
    print(list)
    print("Tisk listu:")
    
    
    print("Klasicky vypis:")
    for list in list:
        print(list)
        
    my_instances = session.get_all_instances()
    print("Klasicky vypis:")
    for item in session.get_all_instances():
        print(f"Id: {item.id}, ObjektID: {id(item)}")
    
    session.remove_instance(5)
    
    for item in session.get_all_instances():
        print(f"Id: {item.id}, Objekt: {item}")
        
    session.remove_instance(5)
    for item in session.get_all_instances():
        print(f"Id: {item.id}, Objekt: {item}")
    
    to_destroy = Session.get_instance(1)
    Session.remove_instance(to_destroy)
    
    for item in session.get_all_instances():
        print(f"Id: {item.id}, Objekt: {item}")
    
    for item in session.get_all_instances():
        if item.id == 9:
            session.remove_instance(0,item)
            
    for item in session.get_all_instances():
        print(f"Id: {item.id}, Objekt: {item}")
            
            
            
