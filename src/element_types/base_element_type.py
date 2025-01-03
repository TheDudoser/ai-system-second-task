from enum import Enum


class BaseElementType(str, Enum):
    def normalize(self):
        return self.value.replace(' ', '_')
