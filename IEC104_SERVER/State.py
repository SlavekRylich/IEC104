from enum import Enum

class StateConn(Enum):
    Disconnected = 0
    Connected = 1
    
    def __str__(self):
        return self.name

    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value
    
class StateTrans(Enum):
    Stopped = 0
    Pending_running = 1
    Running = 2
    Pending_unconfirmed = 3
    Pending_stopped = 4
    
    def __str__(self):
        return self.name
    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value
        
    