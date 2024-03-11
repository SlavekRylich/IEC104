import asyncio
import time


from Frame import Frame
from QueueManager import QueueManager
from Parser import Parser
from Session import Session

    
class PacketBuffer:
    def __init__(self):
        self._buffer: dict[Frame] = {}

    def add_packet(self, packet_id, packet):
        self._buffer[packet_id] = packet

    def get_packet(self, packet_id):
        return self._buffer.get(packet_id)

    def remove_packet(self, packet_id):
        del self._buffer[packet_id]

    def has_packet(self, packet_id):
        return packet_id in self._buffer

    def clear(self):
        self._buffer.clear()

    def __len__(self):
        return len(self._buffer)
