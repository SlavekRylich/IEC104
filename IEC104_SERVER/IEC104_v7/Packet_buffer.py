# -*- coding: utf-8 -*-

import logging

from Frame import Frame


class PacketBuffer:
    def __init__(self):
        self.__buffer: dict[int, Frame] = {}

    def add_frame(self, frame_id: int, frame: Frame) -> None:
        self.__buffer[frame_id] = frame

    def get_frame(self, frame_id: int) -> Frame:
        return self.__buffer.get(frame_id)

    def remove_frame(self, frame_id: int) -> None:
        del self.__buffer[frame_id]

    def has_frame(self, frame_id: int) -> bool:
        return frame_id in self.__buffer

    def clear_frames_less_than(self, frame_id: int) -> None:
        for key, frame in list(self.__buffer.items()):
            if isinstance(frame, Frame):
                if key <= frame_id:
                    print(f"del {key}, {frame}")
                    logging.debug(f"del {key}, {frame}")
                    del self.__buffer[key]

    def get_list_from_buffer(self) -> list:
        return list(self.__buffer.values())

    def is_empty(self) -> int:
        return len(self.__buffer) == 0

    def clear(self) -> None:
        self.__buffer.clear()

    def __len__(self) -> int:
        return len(self.__buffer)
