from ecp import *
import sys as _sys
class sys(BuiltinModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = {
            "path": Interpreter.__interpreter__.path
        }