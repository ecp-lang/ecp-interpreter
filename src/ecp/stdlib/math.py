from ecp import *
import math as _math
class math(BuiltinModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = {
            "sqrt": self.sqrt
        }
    
    def sqrt(self, v: Object):
        return Object.create(_math.sqrt(v.value))