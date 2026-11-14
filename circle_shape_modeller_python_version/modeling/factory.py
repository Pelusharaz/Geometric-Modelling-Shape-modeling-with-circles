from .hermite_envelope import HermiteEnvelope
from .disk_bezier import DiskBezier
class ModelingFactory:
    _methods={'Hermite Circle Envelope':HermiteEnvelope,'Disk-Bézier':DiskBezier}
    @classmethod
    def names(cls): return list(cls._methods)
    @classmethod
    def create(cls,name):
        if name not in cls._methods: raise ValueError(f'Unknown modelling method: {name}')
        return cls._methods[name]()
