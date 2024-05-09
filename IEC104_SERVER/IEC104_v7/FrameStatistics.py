import time
from collections import Counter
from statistics import mean

from Frame import Frame
from IFormat import IFormat


class FrameStatistics:
    def __init__(self, ip_add: str, port: int = 0, title: str = ""):
        self.ip_add = ip_add
        self.port = port

        self.send_frame_count = 0
        self.send_frame_bytes = 0
        self.send_transfer_times = []
        self.send_frame_types = Counter()

        self.recv_frame_count = 0
        self.recv_frame_bytes = 0
        self.recv_transfer_times = []
        self.recv_frame_types = Counter()

        self.allow_statistics = True
        self.own_rules: dict[str, int] = {}
        self.title = title

    def get_ip_add(self) -> str:
        return self.ip_add

    def get_port(self) -> int:
        return self.port

    def allow_stats(self, option: bool) -> None:
        self.allow_statistics = option

    def update_send(self, frame: Frame = None, name: str = None):
        if self.allow_statistics:
            frame_type = frame.type_in_word
            # Zpracujte příchozí rámec

            # Aktualizujte počítadla
            self.send_frame_count += 1
            self.send_frame_bytes += frame.length
            # self.send_transfer_times.append(time.time() - start_time)
            self.send_frame_types[frame_type] += 1

            for item in self.own_rules.keys():
                if name == item:
                    self.own_rules[item] += 1

    def update_recv(self, frame: Frame = None, name: str = None):
        if self.allow_statistics:
            frame_type = frame.type_in_word

            # Aktualizujte počítadla
            self.recv_frame_count += 1
            self.recv_frame_bytes += frame.length
            # self.recv_transfer_times.append(time.time() - start_time)
            self.recv_frame_types[frame_type] += 1

            for item in self.own_rules.keys():
                if name == item:
                    self.own_rules[item] += 1

    def reset_statistics(self):
        # Resetujte statistiky
        self.send_frame_count = 0
        self.send_frame_bytes = 0
        self.send_transfer_times = []
        self.send_frame_types = Counter()

        self.recv_frame_count = 0
        self.recv_frame_bytes = 0
        self.recv_transfer_times = []
        self.recv_frame_types = Counter()

        for item in self.own_rules.keys():
            self.own_rules[item] = 0

    def create_rule(self, name: str, value: int = 0):
        self.own_rules[name] = value

    def get_statistics(self):
        # Vraťte statistiky
        return {
            "frame_count": self.frame_count,
            "average_transfer_time": mean(self.transfer_times),
            "frame_types": self.frame_types,
        }

    def __str__(self) -> str:
        return (f"{self.title} - Statistics send:\n"
                f"frame_count: {self.send_frame_count}\n"
                f"frame_bytes: {self.send_frame_bytes}B\n"
                # f" average_transfer_time: {mean(self.send_transfer_times)},"
                f" frame_types: {self.send_frame_types}\n"
                
                f"{self.title} - Statistics receive:\n"
                f"frame_count: {self.recv_frame_count}\n"
                f"frame_bytes: {self.recv_frame_bytes}B\n"
                # f" average_transfer_time: {mean(self.recv_transfer_times)},"
                f" frame_types: {self.recv_frame_types}"
                )

    # packet_counts = [[0 for _ in range(60)] for _ in range(24)]  # 24 hodin, 60 sekund v hodině
    #
    # # Zpracujte příchozí pakety a aktualizujte počítadla
    # def handle_incoming_packet(packet):
    #     current_time = time.time()
    #     hour = int(current_time // 3600)
    #     minute = int((current_time % 3600) // 60)
    #     second = int(current_time % 60)
    #
    #     packet_counts[hour][minute][second] += 1
