import asyncio
import logging
import time


from Frame import Frame

    
class PacketBuffer:
    def __init__(self):
        self.__buffer: dict[int,Frame] = {}

    def add_frame(self, frame_id, frame):
        self.__buffer[frame_id] = frame

    def get_frame(self, frame_id):
        return self.__buffer.get(frame_id)

    def remove_frame(self, frame_id):
        del self.__buffer[frame_id]

    def has_frame(self, frame_id):
        return frame_id in self.__buffer
    
    async def clear_frames_less_than(self, frame_id):
        for key,frame in list(self.__buffer.items()):
            if isinstance(frame, Frame):
                if key <= frame_id:
                    print(f"del {key}, {frame}")
                    logging.debug(f"del {key}, {frame}")
                    del self.__buffer[key]
    
    def get_list_from_buffer(self):
        return list(self.__buffer.values())
    
    def is_empty(self):
        return len(self.__buffer) == 0

    def clear(self):
        self.__buffer.clear()

    def __len__(self):
        return len(self.__buffer)
