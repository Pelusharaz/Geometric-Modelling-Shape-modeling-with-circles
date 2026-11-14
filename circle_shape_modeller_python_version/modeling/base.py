from abc import ABC, abstractmethod
class ShapeModelingMethod(ABC):
    name = 'Base method'
    @abstractmethod
    def generate(self, circles, resolution=80): ...
