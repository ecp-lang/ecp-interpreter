from tabulate import tabulate
from typing import *
from collections.abc import Callable
import sys

class VarContainer:
    def __init__(self, onchange: Callable):
        self._onchange = onchange

    def __setattr__(self, name, value):
        if name != "_onchange":
            self._onchange(name, value)
        super(VarContainer, self).__setattr__(name, value)

class Tracker:
    def __init__(self, variables: List[str], compact=False):
        self.values = {}
        self.line = 0
        self.compact = compact
        self.variables = variables
    
    def onchange(self, name, value):
        #print(f"{name} -> {value}")
        if name in self.variables:
            data: dict = self.values.get(name, {})
            
            #while self.line in data.keys():
            if data.get(self.line) != None or not self.compact:
                self.line += 1
            
            data[self.line] = value
    
            self.values[name] = data
    def displayTraceTable(self, variables: List[str] = None, tablefmt="github") -> str:
        headers = list(self.values.keys())
        if variables:
            headers = variables
        
        maxLine = 0
        for v in self.values.values():
            for line in v.keys():
                if line > maxLine:
                    maxLine = line
        
        
        table = []
        for i in range(maxLine+1):
            row = []
            for h in headers:
                row.append(self.values.get(h, {}).get(i, ""))
            table.append(row)
        return tabulate(table, headers=headers, tablefmt=tablefmt)

class Tracer(Tracker):
    def __init__(self, variables: List[str], **kwargs):
        super().__init__(variables, **kwargs)
        self.variables = variables
    
    def tracer(self, frame, event, arg = None):
        code = frame.f_code
        line_no = frame.f_lineno
        #self.onchange("_line_number", line_no)
        for v in self.variables:
            if len(self.values.get(v, {}).keys()) > 0:
                if self.values[v][max(self.values[v].keys())] == frame.f_locals.get(v):
                    continue
            if v in frame.f_locals.keys():
                self.onchange(v, frame.f_locals.get(v))
        return self.tracer

    def __enter__(self):
        sys.settrace(self.tracer)
        return self
    
    def __exit__(self, *args):
        print(self.displayTraceTable())
        sys.settrace(None)