from enum import Enum


class BaseElementType(Enum):
    def normalize(self):
        return self.value.replace(' ', '_')
