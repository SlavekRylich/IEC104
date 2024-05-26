import time
from collections import Counter
from statistics import mean

from Frame import Frame
from IFormat import IFormat


class FrameStatistics:
    """
    This class is responsible for collecting and presenting statistics about the frames sent and received.
    """

    def __init__(self, ip_add: str, port: int = 0, title: str = ""):
        """
        Initialize a new instance of FrameStatistics.

        :param ip_add: The IP address of the device.
        :param port: The port number of the device.
        :param title: The title of the statistics.
        """
        self.__ip_add: str = ip_add
        self.__port: int = port

        self.__send_frame_count: int = 0
        self.__send_frame_bytes: int = 0
        self.__send_transfer_times: list = []
        self.__send_frame_types: Counter = Counter()

        self.__recv_frame_count: int = 0
        self.__recv_frame_bytes: int = 0
        self.__recv_transfer_times: list = []
        self.__recv_frame_types: Counter = Counter()

        self.__allow_statistics: bool = True
        self.__own_rules: dict[str, int] = {}
        self.__title: str = title

    def get_ip_add(self) -> str:
        """
        Get the IP address of the device.

        :return: The IP address of the device.
        """
        return self.__ip_add

    def get_port(self) -> int:
        """
        Get the port number of the device.

        :return: The port number of the device.
        """
        return self.__port

    def allow_stats(self, option: bool) -> None:
        """
        Enable or disable statistics collection.

        :param option: True to enable, False to disable.
        """
        self.__allow_statistics = option

    def update_send(self, frame: Frame = None, name: str = None):
        """
        Update the statistics for sent frames.

        :param frame: The sent frame.
        :param name: The name of the frame.
        """
        if self.__allow_statistics:
            frame_type = frame.type_in_word

            self.__send_frame_count += 1
            self.__send_frame_bytes += frame.length
            self.__send_frame_types[frame_type] += 1

            for item in self.__own_rules.keys():
                if name == item:
                    self.__own_rules[item] += 1

    def update_recv(self, frame: Frame = None, name: str = None):
        """
        Update the statistics for received frames.

        :param frame: The received frame.
        :param name: The name of the frame.
        """
        if self.__allow_statistics:
            frame_type = frame.type_in_word

            self.__recv_frame_count += 1
            self.__recv_frame_bytes += frame.length
            self.__recv_frame_types[frame_type] += 1

            for item in self.__own_rules.keys():
                if name == item:
                    self.__own_rules[item] += 1

    def reset_statistics(self):
        """
        Reset all statistics to their initial values.
        """
        self.__send_frame_count = 0
        self.__send_frame_bytes = 0
        self.__send_transfer_times = []
        self.__send_frame_types = Counter()

        self.__recv_frame_count = 0
        self.__recv_frame_bytes = 0
        self.__recv_transfer_times = []
        self.__recv_frame_types = Counter()

        for item in self.__own_rules.keys():
            self.__own_rules[item] = 0

    def create_rule(self, name: str, value: int = 0):
        """
        Create a new rule for the statistics.

        :param name: The name of the rule.
        :param value: The initial value of the rule.
        """
        self.__own_rules[name] = value

    def __str__(self) -> str:
        """
        Get a string representation of the statistics.

        :return: The string representation of the statistics.
        """
        return (f"{self.__title} - Statistics send:\n"
                f"frame_count: {self.__send_frame_count}\n"
                f"frame_bytes: {self.__send_frame_bytes}B\n"
                # f" average_transfer_time: {mean(self.send_transfer_times)},"
                f" frame_types: {self.__send_frame_types}\n"
                
                f"{self.__title} - Statistics receive:\n"
                f"frame_count: {self.__recv_frame_count}\n"
                f"frame_bytes: {self.__recv_frame_bytes}B\n"
                # f" average_transfer_time: {mean(self.recv_transfer_times)},"
                f" frame_types: {self.__recv_frame_types}"
                )
