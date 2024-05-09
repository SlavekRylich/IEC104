# -*- coding: utf-8 -*-

from typing import Any

from apci import APCI


class Frame:
    # třídní proměná pro uchování unikátní id každé instance
    _id: int = 0
    _instances: list['Frame'] = []
    _start_byte: int = APCI.START_BYTE

    def __init__(self, type_frame='Frame'):
        self._header_length: int = APCI.ACPI_HEADER_LENGTH
        self._total_length: int = self._header_length
        self._structure: bytes | None = None
        self._type_in_word: str = type_frame
        self._direction: str | None = None

        Frame._id += 1
        self._id: int = Frame._id
        Frame._instances.append(self)

    def is_structured(self) -> bool:
        if not self.structure:
            return False
        return True

    @property
    def id(self) -> int:
        return self._id

    @property
    def type_in_word(self) -> str:
        return self._type_in_word

    @classmethod
    def remove_instance(cls, id_instance=0, instance=None) -> list['Frame']:
        instances_to_remove = []

        for inst in cls._instances:
            if inst._id == id_instance or inst == instance:
                instances_to_remove.append(inst)

        for inst in instances_to_remove:
            cls._instances.remove(inst)

        return instances_to_remove

    @classmethod  # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id_instance=0, instance=None) -> bool:
        if not id_instance:  # zde rezerva*
            if instance:
                cls._instances.remove(instance)
                return True
            else:
                return False

        if id_instance < len(cls._instances):
            del cls._instances[id_instance]
            return True
        else:
            return False

    @classmethod
    def get_all_instances(cls) -> list:
        return cls._instances

    def serialize(self) -> Any:
        print(f"This never become")
        # it will return false because method is overrided

    @property
    def length(self) -> int:
        return self._total_length

    # opravit korektne, toto je spatny vypocet delky!!!
    @length.setter
    def length(self, length):
        self._total_length += length

    def get_length_of_data(self) -> int:
        return self._total_length - APCI.ACPI_HEADER_LENGTH

    @property
    def structure(self) -> bytes:
        # here is specify format for each format 
        return self._structure

    @structure.setter
    def structure(self, structure) -> None:
        # here is specify format for each format 
        self._structure = structure

    @classmethod
    def start_byte(cls) -> int:
        return APCI.START_BYTE

    def __str__(self) -> str:
        return f"Typ: {self._type_in_word}, Data in bytes: {self.serialize()}"
