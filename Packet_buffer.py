# -*- coding: utf-8 -*-

import logging

from Frame import Frame


class PacketBuffer:
    """
    A class to manage a buffer of frames.
    """

    def __init__(self):
        """
        Initialize an empty dictionary to store frames.
        """
        self.__buffer: dict[int, Frame] = {}

    def add_frame(self, frame_id: int, frame: Frame) -> None:
        """
        Add a frame to the buffer.

        Parameters:
        frame_id (int): The unique identifier of the frame.
        frame (Frame): The frame object to be added.
        """
        self.__buffer[frame_id] = frame

    def get_frame(self, frame_id: int) -> Frame:
        """
        Retrieve a frame from the buffer based on its unique identifier.

        Parameters:
        frame_id (int): The unique identifier of the frame.

        Returns:
        Frame: The frame object if found, otherwise None.
        """
        return self.__buffer.get(frame_id)

    def remove_frame(self, frame_id: int) -> None:
        """
        Remove a frame from the buffer based on its unique identifier.

        Parameters:
        frame_id (int): The unique identifier of the frame.
        """
        del self.__buffer[frame_id]

    def has_frame(self, frame_id: int) -> bool:
        """
        Check if a frame exists in the buffer based on its unique identifier.

        Parameters:
        frame_id (int): The unique identifier of the frame.

        Returns:
        bool: True if the frame exists, otherwise False.
        """
        return frame_id in self.__buffer

    def clear_frames_less_than(self, frame_id: int) -> None:
        """
        Remove all frames from the buffer with identifiers less than or equal to the given frame_id.

        Parameters:
        frame_id (int): The unique identifier of the frame.
        """
        for key, frame in list(self.__buffer.items()):
            if isinstance(frame, Frame):
                if key <= frame_id:
                    logging.debug(f"del {key}, {frame}")
                    del self.__buffer[key]

    def get_list_from_buffer(self) -> list:
        """
        Retrieve a list of all frames in the buffer.

        Returns:
        list:  A list of frame objects.
        """
        return list(self.__buffer.values())

    def is_empty(self) -> int:
        """
        Check if the buffer is empty.

        Returns:
        bool: True if the buffer is empty, otherwise False.
        """
        return len(self.__buffer) == 0

    def clear(self) -> None:
        """
        Remove all frames from the buffer.
        """
        self.__buffer.clear()

    def __len__(self) -> int:
        """
        Get the number of frames in the buffer.

        Returns:
        int: The number of frames in the buffer.
        """
        return len(self.__buffer)
