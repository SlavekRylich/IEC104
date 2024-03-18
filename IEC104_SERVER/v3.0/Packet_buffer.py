import asyncio
import time


from Frame import Frame

    
class PacketBuffer:
    def __init__(self):
        self._buffer: dict[int,Frame] = {}

    def add_frame(self, frame_id, frame):
        self._buffer[frame_id] = frame

    def get_frame(self, frame_id):
        return self._buffer.get(frame_id)

    def remove_frame(self, frame_id):
        del self._buffer[frame_id]

    def has_frame(self, frame_id):
        return frame_id in self._buffer
    
    async def clear_frames_less_than(self, frame_id):
        for key,frame in list(self._buffer.items()):
            if isinstance(frame, Frame):
                if key <= frame_id:
                    print(f"del {key}, {frame}")
                    del self._buffer[key]
    
    def is_empty(self):
        return len(self._buffer) == 0

    def clear(self):
        self._buffer.clear()

    def __len__(self):
        return len(self._buffer)
