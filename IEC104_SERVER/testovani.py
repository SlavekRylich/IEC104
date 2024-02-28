from enum import Enum

import acpi

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
today = Days.set_day(1)
if today.get_day() == 4:
    print(f'Today is now {today}, which corresponds to {today.get_day()}')
    

if not today == 'MONDAY':
    print(f'1oday is now {today}, which corresponds to {today.get_day()}')
    
text = 'S-format'
def getName():
    return text
def funkce (frame):
    if frame == '0x07':
        print(f"bere to cislo")
        
    if frame == 'S-format':
        print(f"bere to text")
        
funkce(str(acpi.STARTDT_ACT))
funkce(text)
        
