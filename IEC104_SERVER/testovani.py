from enum import Enum

class Days(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    def __str__(self):
        return self.name

    @classmethod
    def set_day(cls, day):
        return cls(day)

    def get_day(self):
        return self.value

# Použití enumerace
today = Days.WEDNESDAY
print(f'Today is {today}')

# Nastavení a získání dne
today = Days.set_day(4)
print(f'Today is now {today}, which corresponds to {today.get_day()}')
