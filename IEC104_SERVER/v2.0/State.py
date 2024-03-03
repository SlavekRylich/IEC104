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
    Waiting_running = 'Waiting_running'
    Running = 'Running'
    Waiting_unconfirmed = 'Waiting_unconfirmed'
    Waiting_stopped = 'Waiting_stopped'
    
    def __str__(self):
        return self.name
    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value
        
    