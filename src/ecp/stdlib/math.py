from ecp import *
import math as _math
class math(BuiltinModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.functions = ['acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh', 'ceil', 'comb', 'copysign', 'cos', 'cosh', 'degrees', 'dist', 'erf', 'erfc', 'exp', 'expm1', 'fabs', 'factorial', 'floor', 'fmod', 'frexp', 'fsum', 'gamma', 'gcd', 'hypot', 'isclose', 'isfinite', 'isinf', 'isnan', 'isqrt', 'ldexp', 'lgamma', 'log', 'log10', 'log1p', 'log2', 'modf', 'perm', 'pow', 'prod', 'radians', 'remainder', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'trunc']
        self.properties = {
            "e": Object.create(_math.e),
            "pi": Object.create(_math.pi),
            "tau": Object.create(_math.pi),
            "nan": Object.create(_math.nan),
            "inf": Object.create(_math.inf)
        }

        for f in self.functions:
            self.properties[f] = self.createSubroutine(f)
    
    def createSubroutine(self, name):
        t = getattr(_math, name)
        def subroutine(*args):
            return Object.create(t(*[v.value for v in args]))
        
        return subroutine