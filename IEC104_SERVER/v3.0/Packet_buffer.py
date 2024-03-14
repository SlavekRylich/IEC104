import asyncio
import time


from Frame import Frame

    
class PacketBuffer:
    def __init__(self):
        self._buffer: dict[Frame] = {}

    def add_frame(self, frame_id, frame):
        self._buffer[frame_id] = frame

    def get_frame(self, frame_id):
        return self._buffer.get(frame_id)

    def remove_frame(self, frame_id):
        del self._buffer[frame_id]

    def has_frame(self, frame_id):
        return frame_id in self._buffer
    
    def clear_frames_less_than(self, frame_id):
        for frame in self._buffer.values():
            if frame.get_id() <= frame_id:
                del self._buffer[frame.get_id()]
    
    def is_empty(self):
        return len(self._buffer) == 0

    def clear(self):
        self._buffer.clear()

    def __len__(self):
        return len(self._buffer)
