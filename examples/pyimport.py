from ecp import *
import math
class pyimport(BuiltinModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = {
            "sqrt": self.sqrt
        }
    
    def sqrt(self, v: Object):
        return Object.create(math.sqrt(v.value))