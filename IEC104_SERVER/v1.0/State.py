from enum import Enum

class StateConn(Enum):
    Disconnected = 'Disconnected'
    Connected = 'Connected'
    
    def __str__(self):
        return self.name

    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value
    
class StateTrans(Enum):
    Stopped = 'Stopped'
    Pending_running = 'Pending_running'
    Running = 'Running'
    Pending_unconfirmed = 'Pending_unconfirmed'
    Pending_stopped = 'Pending_stopped'
    
    def __str__(self):
        return self.name
    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value
        
    