from .lexer import *
import random
import math
from pprint import pprint
from typing import *
from copy import deepcopy
import os
import glob
import importlib.util
import inspect

"""
ECP full grammar

program               :  statement_list EOF

compound              :  statement_list

statement_list        :  (statement)*

statement             :  assignment_statement
                      |  magic_function
                      |  subroutine_call
                      |  subroutine
                      |  if_statement
                      |  while_loop
                      |  repeat_until_loop
                      |  for_loop

assignment_statement  :  variable ASSIGN expr

magic_function        :  MAGIC ( expr ( COMMA expr )* )?

subroutine_call       :  variable LPAREN ( param ( COMMA param )* )? RPAREN

param                 :  expr

subroutine            :  SUBROUTINE ID LPAREN ( param_definition ( COMMA parem_definition )* )? RPAREN compound ENDSUBROUTINE
param_definition      :  variable


if_statement          :  IF condition THEN compound ( else_if_statement | else_statement )? ENDIF
else_if_statement     :  ELSE if_statement
else_statement        :  ELSE compound

for_loop              :  FOR assignment_statement TO expr (STEP expr)? compound ENDFOR
                      |  FOR variable IN expr compound ENDFOR

while_loop            :  WHILE expr compound ENDWHILE

repeat_until_loop     :  REPEAT compound UNTIL expr

record_definition     :  RECORD ID (variable)* ENDRECORD

class_definition      :  CLASS ( subroutine | assignment_statement ) ENDCLASS

import_statement      :  IMPORT expr (AS expr)

try_catch             :  TRY compound CATCH compound ENDTRY

expr                  :  term5

term5                 :  term4  ( ( AND | OR            ) term4  )*
term4                 :  term3  ( ( EQALITY_OP          ) term3  )*
term3                 :  term2  ( ( ADD | SUB           ) term2  )*
term2                 :  term   ( ( MUL | DIV | INT_DIV ) term   )*
term                  :  factor ( ( POW | MOD           ) factor )*

EQUALITY_OP           :  ( LT | LE | EQ | NE | GT | GE )


factor                :  PLUS factor
                      |  MINUS factor
                      |  INTEGER_CONST
                      |  REAL_CONST
                      |  LPAREN expr RPAREN
                      |  TRUE
                      |  FALSE
                      |  variable
                      |  function_call
                      |  array

array                 :  LS_PAREN (expr (COMMA expr)*)? RS_PAREN

dictionary            :  LC_BRACE ((expr COLON expr) (COMMA expr COLON expr)*)? RC_BRACE

variable              :  (CONSTANT)? ID (targeter)* (COLON TYPE)?

targeter              :  LS_PAREN expr RS_PAREN



NOTE:
The priority for math operations is as follows:
    - HIGHEST PRECEDENCE -
    factor :  (this can be seen as the final stage, where brackets are prcoessed etc)
    term   :  pow     (right-associative operator)
    term2  :  mul, div, int_div, mod
    term3  :  add, sub
    term4  :  lt, le, eq, ne, gt, ge
    term5  :  and, or
    - LOWEST PRECEDENCE -
"""



class AST(object):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr


class Compound(AST):
    """Represents a 'BEGIN ... END' block"""
    def __init__(self):
        self.children = []


class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Var(AST):
    """The Var node is constructed out of ID token."""
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.indexes = []


class Magic(AST):
    def __init__(self, token, parameters):
        self.token = token
        self.parameters = parameters


class DeclaredParam(AST):
    def __init__(self, variable, default):
        self.variable = variable
        self.default = default


class Param(AST):
    def __init__(self, value, id):
        self.value = value
        self.id = id


class Subroutine(AST):
    def __init__(self, token, parameters, compound):
        self.token = token
        self.parameters = parameters
        self.compound = compound
        self.builtin = False
        self.classBase = None
        self.scopeBase = None


class SubroutineDefinition(Subroutine):
    pass


class SubroutineCall(AST):
    def __init__(self, subroutine_token, parameters):
        self.subroutine_token = subroutine_token
        self.parameters = parameters


class Import(AST):
    def __init__(self, location, target):
        self.location = location
        self.target = target


class PropertyIndex(AST):
    def __init__(self, node):
        self.node = node


class ValueIndex(AST):
    def __init__(self, node):
        self.node = node


class IndexedItem(AST):
    def __init__(self, node: AST, indexes: List[Union[PropertyIndex, ValueIndex]]):
        self.node = node
        self.indexes = indexes


class NoOp(AST):
    pass


class Object(AST):
    def __init__(self, value):
        self.value = value
        self.properties = {}
    
    def __add__(self, other):
        return Object.create(self.value + other.value)
    
    def __sub__(self, other):
        return Object.create(self.value - other.value)
    
    def __mul__(self, other):
        return Object.create(self.value * other.value)

    def __div__(self, other):
        return Object.create(self.value / other.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)
    
    def __get__(self, key, default):
        if isinstance(key, Object):
            return self.properties[key.value]
        return self.properties[key]
    
    def __set__(self, key, value):
        if isinstance(key, Object):
            self.properties[key.value] = value
        else:
            self.properties[key] = value
    
    def __getitem__(self, index):
        if isinstance(index, Object):
            index = index.value
        if isinstance(index, int):
            return self.value[index]
        else:
            return self.properties[index]
    
    def __setitem__(self, index, value):
        if isinstance(index, Object):
            index = index.value
        if isinstance(index, int):
            self.value[index] = value
        else:
            self.properties[index] = value
    
    def __hash__(self):
        return hash(self.value)
    
    def __eq__(self, other):
        if isinstance(other, Object):
            return self.value == other.value
        else:
            return other.__eq__(self.value)
    
    def __ne__(self, other):
        return not (self == other)
    
    @staticmethod
    def create(value):
        t = Object.associations.get(type(value).__name__)
        if not t:
            return value
        return Object.associations[type(value).__name__](value)

class IntObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__(int(value.value))
        else:
            super().__init__(int(value))

class FloatObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__(float(value.value))
        else:
            super().__init__(float(value))

class BoolObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__(bool(value.value))
        else:
            super().__init__(bool(value))

class StringObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__(str(value.value))
        else:
            super().__init__(str(value))

class ArrayObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__([Object.create(o) for o in value.value]) # make sure all elements are objects
        else:
            super().__init__([Object.create(o) for o in value])
        self.properties = {
            "append": self.append
        }
    
    def __str__(self):
        return f"[{', '.join([repr(Interpreter.__interpreter__.visit(i)) for i in self.value])}]"

    def append(self, _object):
        self.value.append(_object)

class DictionaryObject(Object):
    def __init__(self, value):
        if isinstance(value, Object):
            super().__init__(dict(value.value))
        else:
            super().__init__(dict(value))
    
    def __get__(self, key, default):
        return self.value[key]
    
    def __set__(self, key, value):
        self.value[key] = value
    
    def __getitem__(self, index):
        return self.value[index]
    
    def __setitem__(self, index, value):
        self.value[index] = value


class NoneObject(Object):
    def __init__(self, value=None):
        super().__init__(None)


class Record(Object):
    def __init__(self, token):
        super().__init__(None)
        self.token = token
        self.parameters = []
    
    def __str__(self):
        return f"<record definition {self.token.value}>"

class RecordObject(Object):
    def __init__(self, base: Record):
        super().__init__(None)
        self.base = base
        self.properties = {}
    
    def __str__(self):
        return f"<record object {self.base.token.value}>"

class ClassDefinition(Object):
    special_subroutines = [
        "STR", "REPR",
        "INIT",
    ]

    def __init__(self, token: Var, static_values: List[Assign], subroutines: List[Subroutine]):
        super().__init__(None)
        self.token = token
        self.static_values = static_values
        self.subroutines = subroutines
    
    def __str__(self):
        if "STR" in self.properties:
            return str(Interpreter.__interpreter__.visit(SubroutineCall(self.properties["STR"], [])))
        return f"<class definition {self.token.value}>"
    
    def __repr__(self):
        if "REPR" in self.properties:
            return str(Interpreter.__interpreter__.visit(SubroutineCall(self.properties["REPR"], [])))
        return self.__str__()

class ClassInstance(Object):
    def __init__(self, base: ClassDefinition):
        super().__init__(None)
        self.base = base
        self.properties = deepcopy(base.properties)
    
    def __str__(self):
        if "STR" in self.properties:
            return str(Interpreter.__interpreter__.visit(SubroutineCall(self.properties["STR"], [])))
        return f"<class instance {self.base.token.value}>"
    
    def __repr__(self):
        if "REPR" in self.properties:
            return str(Interpreter.__interpreter__.visit(SubroutineCall(self.properties["REPR"], [])))
        return self.__str__()

class BuiltinModule(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __str__(self):
        return f"<BuiltinModule '{type(self).__name__}'>"
    
    def __repr__(self):
        return f"<BuiltinModule '{type(self).__name__}'>"

Object.associations = {
    "int":       IntObject,
    "float":     FloatObject,
    "bool":      BoolObject,
    "str":       StringObject,
    "list":      ArrayObject,
    "tuple":      ArrayObject,
    "dict":      DictionaryObject,
    "NoneType":  NoneObject
}

Object.types = {
    "Integer":    IntObject,
    "Int":        IntObject,
    "Real":       FloatObject,
    "Bool":       BoolObject,
    "String":     StringObject,
    "Array":      ArrayObject,
    "Dictionary": DictionaryObject,
}

TokenConversions = {
    TokenType.INT: int,
    TokenType.FLOAT: float,
    TokenType.BOOLEAN: lambda s: False if s.lower() == "false" else True,
    TokenType.STRING: str,
    TokenType.NONE: lambda s: None
}

        

class ParseError(Exception):
    def __init__(self, msg, lineno, column, lineText=""):
        self.msg = msg
        self.lineno = lineno
        self.column = column
        self.lineText = lineText
    
    def __str__(self):
        ret = f"\n  Line {self.lineno}:\n"
        if self.lineText:
            ret += f"  {self.lineText}\n  {' '*(self.column-1)}^\n"
        return ret + f"{self.msg}"

class InterpreterError(Exception):
    pass

class IfStatement(AST):
    def __init__(self, condition):
        self.condition = condition
        self.consequence = []
        self.alternatives = []
    

class WhileStatement(AST):
    def __init__(self, condition):
        self.condition = condition
        self.consequence = []

class ForLoop(AST):
    def __init__(self, variable, iterator):
        self.variable = variable
        self.iterator = iterator
        self.to_step = False
        self.start = None
        self.end = None
        self.step = None
        self.loop = []

class RepeatUntilStatement(WhileStatement):
    pass

class TryCatch(AST):
    def __init__(self, try_compound, catch_compound):
        self.try_compound = try_compound
        self.catch_compound = catch_compound

#class BuiltinType(object):
#    def __init__(self, value):
#        self.value = value
#
#class Int(BuiltinType):
#    def __init__(self, value):
#        super().__init__(value)
#
#    def __add__(self, other):
#        return Int(self.value + other.value)

class Parser:
    def __init__(self, lexer: LexerResult):
        self.nodes = {}
        self.offset = 0
        self.lexer = lexer
        self.token_num = 0
    
    def EOF(self):
        return Token("", TokenType.EOF, len(self.lexer.lines)-1, len(self.lexer.lines[-2])+1)
    
    def get_next_token(self):
        self.token_num += 1
        if self.token_num >= len(self.lexer.tokens):
            return self.EOF()
        return self.lexer.tokens[self.token_num]
    
    
    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.get_next_token()
        else:
            raise ParseError(
                f"Expected {token_type} but found {self.current_token.error_format()}",
                *self.current_token.pos,
                lineText=self.lexer.lines[self.current_token.lineno-1]
            )

    def eat_gap(self):
        while self.current_token.type in (TokenType.NEWLINE,):
            self.eat(self.current_token.type)


    @property
    def current_token(self):
        if self.token_num >= len(self.lexer.tokens):
            return self.EOF()
        return self.lexer.tokens[self.token_num]
    
    @property
    def next_token(self):
        if self.token_num + 1 >= len(self.lexer.tokens):
            return self.EOF()
        return self.lexer.tokens[self.token_num + 1]
    
    def error(self):
        raise ParseError(
            f"Unexpected token {self.current_token.error_format()}", 
            *self.current_token.pos,
            lineText=self.lexer.lines[self.current_token.lineno-1]
        )

    def program(self):
        
        return self.compound()
    
    def compound(self):
        nodes = self.statement_list()
        node = Compound()
        node.children = nodes

        return node
    
    def statement_list(self):
        results = []
        self.eat_gap()
        if self.current_token.type != TokenType.NEWLINE:
            node = self.statement()
            if node:
                results.append(node)
            

        while self.current_token.type == TokenType.NEWLINE:
            self.eat_gap()
            node = self.statement()
            if node:
                results.append(node)

        if self.current_token.type == TokenType.ID:
            self.error()

        return results
    
    def statement(self):
        if self.current_token.type in (TokenType.ID, TokenType.CONSTANT):
            var = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(var)
            elif self.current_token.type == TokenType.ASSIGN:
                # only happen if next token is assignment
                node = self.assignment_statement(var)
            else:
                node = var
        elif self.current_token.type == TokenType.MAGIC:
            node = self.magic_function()
        elif self.current_token.type == TokenType.IF:
            node = self.if_statement()
            self.eat(TokenType.KEYWORD)
            return node
        elif self.current_token.type == TokenType.WHILE:
            node = self.while_statement()
            self.eat(TokenType.KEYWORD)
            return node
        elif self.current_token.type == TokenType.REPEAT:
            return self.repeat_until_statement()
        elif self.current_token.type == TokenType.FOR:
            return self.for_loop()
        elif self.current_token.type == TokenType.RECORD:
            return self.record_definition()
        elif self.current_token.type == TokenType.TRY:
            return self.try_catch()
        elif self.current_token.type == TokenType.SUBROUTINE:
            return self.subroutine()
        elif self.current_token.type == TokenType.CLASS:
            return self.class_definition()
        elif self.current_token.type == TokenType.IMPORT:
            return self.import_statement()
        else: # expr
            return self.expr()

        while self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN, TokenType.LPAREN):
            if self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN):
                node = self.process_indexing(node)
            else:
                node = self.subroutine_call(node)
        
        return node
    
    def assignment_statement(self, var):
        left = var
        token = self.current_token
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.ID) # TYPE
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = Assign(left, token, right)
        return node
    
    def variable(self):
        if self.current_token.type == TokenType.CONSTANT:
            self.eat(TokenType.CONSTANT)
        node = Var(self.current_token)
        self.eat(TokenType.ID)
        while self.current_token.type in (TokenType.LS_PAREN, TokenType.DOT):
            if self.current_token.type == TokenType.LS_PAREN:
                self.eat(TokenType.LS_PAREN)
                node.indexes.append(ValueIndex(self.expr()))
                self.eat(TokenType.RS_PAREN)
            elif self.current_token.type == TokenType.DOT:
                self.eat(TokenType.DOT)
                node.indexes.append(PropertyIndex(self.id()))
        return node
    
    def process_indexing(self, node):
        # should split into types
        indexes = []
        while self.current_token.type in (TokenType.LS_PAREN, TokenType.DOT):
            if self.current_token.type == TokenType.LS_PAREN:
                self.eat(TokenType.LS_PAREN)
                indexes.append(ValueIndex(self.expr()))
                self.eat(TokenType.RS_PAREN)
            elif self.current_token.type == TokenType.DOT:
                self.eat(TokenType.DOT)
                indexes.append(PropertyIndex(self.id()))
        return IndexedItem(node, indexes)
    
    def id(self):
        token = self.current_token
        self.eat(TokenType.ID)
        return StringObject(token.value)
    
    def empty(self):
        return NoOp()

    def factor(self):
        """factor : PLUS  factor
              | MINUS factor
              | INTEGER
              | FLOAT
              | STRING
              | BOOLEAN
              | LPAREN expr RPAREN
              | variable
              | function_call
              | ARRAY
        """
        token = self.current_token
        if token.type == TokenType.ADD:
            self.eat(TokenType.ADD)
            node = UnaryOp(token, self.factor())
        elif token.type == TokenType.SUB:
            self.eat(TokenType.SUB)
            node = UnaryOp(token, self.factor())
        elif token.type == TokenType.NOT:
            self.eat(TokenType.NOT)
            node = UnaryOp(token, self.factor())
        elif token.type in TokenConversions.keys():
            self.eat(token.type)
            node = Object.create(TokenConversions[token.type](token.value))
        
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
        elif token.type == TokenType.LS_PAREN:
            self.eat(TokenType.LS_PAREN)
            node = self.array()
            self.eat(TokenType.RS_PAREN)
        elif token.type == TokenType.LC_BRACE:
            self.eat(TokenType.LC_BRACE)
            node = self.dictionary()
            self.eat(TokenType.RC_BRACE)
        elif token.type == TokenType.MAGIC:
            node = self.magic_function()
        elif token.type == TokenType.ID:
            node = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(node)
        else:
            return
        
        while self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN, TokenType.LPAREN):
            if self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN):
                # would like to split these so something.something indicates a property and something["something"] is value
                node = self.process_indexing(node)
            else:
                node = self.subroutine_call(node)
        return node

    def term(self):
        node = self.factor()

        if self.current_token.type in (TokenType.POW, ):
            token = self.current_token
            self.eat(token.type)
        
            node = BinOp(left=node, op=token, right=self.term())
        
        return node
    
    def term2(self):
        
        node = self.term()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.INT_DIV, TokenType.MOD):
            token = self.current_token
            self.eat(token.type)
        
            node = BinOp(left=node, op=token, right=self.term())
        
        return node
    

    def term3(self):
        
        node = self.term2()

        while self.current_token.type in (
            TokenType.ADD, TokenType.SUB, 
            #TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE,
        ):
            token = self.current_token
            self.eat(token.type)
            
            node = BinOp(left=node, op=token, right=self.term2())
        
        return node
    
    def term4(self):
        
        node = self.term3()
        while self.current_token.type in (
            TokenType.LT,
            TokenType.GT,
            TokenType.LE,
            TokenType.GE,
            TokenType.EQ,
            TokenType.NE,
        ):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.term3())
        return node
    
    def term5(self):
        
        node = self.term4()
        while self.current_token.type in (
            TokenType.AND, TokenType.OR,
        ):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.term4())
        return node
        
    
    def expr(self):
        return self.term5()

    def magic_function(self):
        token = self.current_token
        self.eat(TokenType.MAGIC)
        parameters = []
        if self.current_token.type not in (TokenType.EOF, TokenType.NEWLINE, TokenType.RPAREN):
            parameters.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.expr())
        node = Magic(token, parameters)

        return node
    
    def declare_param(self):
        var = self.variable()
        node = DeclaredParam(var, None)
        token = self.current_token
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.ID) # TYPE
        #if self.current_token.type == TokenType.ASSIGN:
        #    self.eat(TokenType.ASSIGN)
        #    right = self.expr()
        #    node.default = right
        
        return node
    
    def param(self):
        node = Param(self.expr(), None)
        return node

    
    def subroutine(self):
        self.eat(TokenType.SUBROUTINE)
        token = self.current_token
        self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)
        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            parameters.append(self.declare_param())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.declare_param())
        self.eat(TokenType.RPAREN)
        compound = self.compound()
        self.eat(TokenType.KEYWORD)
        return SubroutineDefinition(token, parameters, compound)

    def subroutine_call(self, var):
        self.eat(TokenType.LPAREN)

        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            parameters.append(self.param())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.param())
        self.eat(TokenType.RPAREN)
        return SubroutineCall(var, parameters)

    def process_keyword(self):
        token = self.current_token
        if False: pass
        else:
            node = self.empty()
        return node
    
    def if_statement(self):
        token = self.current_token
        self.eat(TokenType.IF)

        condition = self.expr()
        self.eat_gap()
        self.eat(TokenType.THEN)

        consequence = self.compound()

        alternatives = []
        if self.current_token.type == TokenType.ELSE and self.next_token.type == TokenType.IF:
            alternatives.append(self.elseif_statement())
        elif self.current_token.type == TokenType.ELSE:
            alternatives.append(self.else_statement())
        
        node = IfStatement(condition=condition)
        node.consequence = consequence
        node.alternatives = alternatives
        return node

    def elseif_statement(self):
        self.eat(TokenType.ELSE)
        return self.if_statement()
    
    def else_statement(self):
        self.eat(TokenType.ELSE)
        return self.compound()
    
    def while_statement(self):
        token = self.current_token
        self.eat(TokenType.WHILE)
        condition = self.expr()
        consequence = self.compound()

        node = WhileStatement(condition)
        node.consequence = consequence

        return node
    
    def repeat_until_statement(self):
        token = self.current_token
        self.eat(TokenType.REPEAT)
        
        consequence = self.compound()
        self.eat_gap()
        self.eat(TokenType.UNTIL)
        condition = self.expr()

        node = RepeatUntilStatement(condition)
        node.consequence = consequence

        return node
    
    def array(self):
        """array  :  LS_PAREN (expr)? (COMMA expr)* RS_PAREN"""
        values = []
        if self.current_token.type != TokenType.RS_PAREN:
            self.eat_gap()
            values.append(self.expr())
            self.eat_gap()
            while self.current_token.type == TokenType.COMMA:
                self.eat_gap()
                self.eat(TokenType.COMMA)
                self.eat_gap()
                values.append(self.expr())
                self.eat_gap()
        self.eat_gap()
        #print(values)
        return ArrayObject(values)
    
    def dictionary(self):
        """ LC_BRACE ((expr COLON expr) (COMMA expr COLON expr)*)?  RC_BRACE """
        values = {}
        if self.current_token.type != TokenType.RC_BRACE:
            self.eat_gap()
            key = self.expr()
            self.eat(TokenType.COLON)
            self.eat_gap()
            value = self.expr()
            values[key] = value
            while self.current_token.type == TokenType.COMMA:
                self.eat_gap()
                self.eat(TokenType.COMMA)
                self.eat_gap()
                key = self.expr()
                self.eat(TokenType.COLON)
                self.eat_gap()
                value = self.expr()
                values[key] = value
                self.eat_gap()
        return DictionaryObject(values)
    
    def for_loop(self):
        """for_loop   : FOR ID ASSIGN expr TO expr (STEP expr)? statement_list ENDFOR
                      | FOR variable IN expr statement_list ENDFOR
        """
        loop = []
        self.eat(TokenType.FOR)
        variable = self.variable()
        f = ForLoop(variable, None)
        if self.current_token.type == TokenType.ASSIGN:
            f.to_step = True
            # FOR ID ASSIGN expr TO expr (STEP expr)? statement_list ENDFOR
            self.eat(TokenType.ASSIGN)
            f.start = self.expr()
            self.eat(TokenType.TO)
            f.end = self.expr()
            if self.current_token.type == TokenType.STEP:
                self.eat(TokenType.STEP)
                f.step = self.expr()
                
            self.eat_gap()
            f.loop = self.compound()
            
        elif self.current_token.type == TokenType.IN:
            # FOR variable IN expr statement_list ENDFOR
            self.eat(TokenType.IN)
            f.iterator = self.expr()
            self.eat_gap()
            f.loop = self.compound()
        
        self.eat(TokenType.KEYWORD)
        return f
    
    def record_definition(self):
        """record_definition  :  RECORD ID (variable)* ENDRECORD"""
        self.eat(TokenType.RECORD)
        token = self.id()
        node = Record(token)
        self.eat_gap()
        while self.current_token.type != TokenType.KEYWORD:
            self.eat_gap()
            node.parameters.append(self.variable().value)
            if self.current_token.type == TokenType.COLON:
                self.eat(TokenType.COLON)
                self.eat(TokenType.ID) # TYPE
            self.eat_gap()
        
        self.eat_gap()
        self.eat(TokenType.KEYWORD)
        return node
    
    def try_catch(self):
        self.eat(TokenType.TRY)
        try_compound = self.compound()
        self.eat(TokenType.CATCH)
        catch_compound = self.compound()
        self.eat(TokenType.KEYWORD)

        return TryCatch(try_compound, catch_compound)
    
    def class_definition(self):
        self.eat(TokenType.CLASS)
        variable = self.variable()
        static_values = []
        subroutines = []
        self.eat_gap()
        while self.current_token.type in (TokenType.SUBROUTINE, TokenType.ID):
            self.eat_gap()
            if self.current_token.type == TokenType.SUBROUTINE:
                subroutines.append(self.subroutine())
            elif self.current_token.type == TokenType.ID:
                v = self.variable()
                static_values.append(self.assignment_statement(v))
            self.eat_gap()
        self.eat_gap()
        self.eat(TokenType.KEYWORD)

        return ClassDefinition(variable, static_values, subroutines)
    
    def import_statement(self):
        self.eat(TokenType.IMPORT)
        location = self.expr()
        target = None
        if self.current_token.type == TokenType.AS:
            self.eat(TokenType.AS)
            target = self.expr()
        return Import(location, target)

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error()

        return node


class VariableScope(object):
    def __init__(self, name, enclosing_scope):
        self.name = name
        self.enclosing_scope = enclosing_scope
        self.properties = {}
    
    def insert(self, var, value):
        if Interpreter.__interpreter__.tracer:
            Interpreter.__interpreter__.tracer.onchange(var.value, value)
        self.properties[var.value] = value
    
    def get(self, var):
        if var.value not in self.properties.keys():
            while self.enclosing_scope != None:
                return self.enclosing_scope.get(var)
        else:
            value = self.properties.get(var.value)
            return value
        raise InterpreterError(f"variable {var.value} does not exist")
    
    def __get__(self, key, default):
        return self.properties[key.value]
    
    def __set__(self, key, value):
        self.properties[key.value] = value
    
    def __getitem__(self, index):
        return self.properties[index.value]
    
    def __setitem__(self, index, value):
        self.properties[index.value] = value

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(node.__class__.__name__))


class _BUILTINS(BuiltinModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = {
            "INPUT":          self.INPUT, 
            "LEN":            self.LEN, 
            "POSITION":       self.POSITION, 
            "SUBSTRING":      self.SUBSTRING, 
            "STRING_TO_INT":  self.STRING_TO_INT, 
            "STRING_TO_REAL": self.STRING_TO_REAL, 
            "INT_TO_STRING":  self.INT_TO_STRING, 
            "REAL_TO_STRING": self.REAL_TO_STRING, 
            "CHAR_TO_CODE":   self.CHAR_TO_CODE, 
            "CODE_TO_CHAR":   self.CODE_TO_CHAR, 
            "RANDOM_INT":     self.RANDOM_INT,
            "SQRT":           self.SQRT,
        }
    
    def INPUT(self, *args):
        return Object.create(input(args[0].value if len(args) > 0 else ""))
    
    def LEN(self, *args):
        return Object.create(len(args[0].value))
    
    def POSITION(self, s: Object, c: Object, *args):
        string = s.value
        to_match = c.value

        try:
            return Object.create(string.index(to_match))
        except ValueError:
            return -1
    
    def SUBSTRING(self, start: Object, end: Object, string: Object, *args):
        start = start.value
        end = end.value
        string = string.value

        return Object.create(string[start:end+1])
    
    def STRING_TO_INT(self, string: Object):
        string = string.value
        return Object.create(int(string))
    
    def STRING_TO_REAL(self, string: Object):
        string = string.value
        return Object.create(float(string))
    
    def INT_TO_STRING(self, integer: Object):
        integer = integer.value
        return Object.create(str(integer))
    
    def REAL_TO_STRING(self, real: Object):
        real = real.value
        return Object.create(str(real))
    
    def CHAR_TO_CODE(self, char: Object):
        char = char.value
        return Object.create(ord(char))
    
    def CODE_TO_CHAR(self, code: Object):
        code = code.value
        return Object.create(chr(code))
    
    def RANDOM_INT(self, a: Object, b: Object):
        a = a.value
        b = b.value

        return Object.create(random.randint(a, b))
    
    def SQRT(self, num: Object):
        num = num.value
        return Object.create(math.sqrt(num))



class Interpreter(NodeVisitor):
    __interpreter__ = None
    def __init__(self, tracer=None, location=None, name=None, stdlib_loc="stdlib"):
        self.current_scope = None
        self.RETURN = False
        self.CONTINUE = False
        self.BREAK = False
        self.tracer = tracer
        self.path = ArrayObject([os.path.join(os.path.dirname(inspect.stack()[0][1]), stdlib_loc)])
        self.location, self.name = None, name
        if location:
            self.path.value.insert(0, StringObject(location))
            self.location = location
            os.chdir(location)
        #print(self.path)

        Interpreter.__interpreter__ = self # hacky solution to allwoing object to access the interpreter
    
    def visit_BinOp(self, node: BinOp):
        if node.op.type == TokenType.ADD:
            result = self.visit(node.left).value + self.visit(node.right).value
        elif node.op.type == TokenType.SUB:
            result = self.visit(node.left).value - self.visit(node.right).value
        elif node.op.type == TokenType.MUL:
            result = self.visit(node.left).value * self.visit(node.right).value
        elif node.op.type == TokenType.DIV:
            result = self.visit(node.left).value / self.visit(node.right).value
        elif node.op.type == TokenType.INT_DIV:
            result = self.visit(node.left).value // self.visit(node.right).value
        elif node.op.type == TokenType.MOD:
            result = self.visit(node.left).value % self.visit(node.right).value
        elif node.op.type == TokenType.POW:
            result = self.visit(node.left).value ** self.visit(node.right).value
        
        elif node.op.type == TokenType.GT:
            result = self.visit(node.left).value > self.visit(node.right).value
        elif node.op.type == TokenType.GE:
            result = self.visit(node.left).value >= self.visit(node.right).value
        elif node.op.type == TokenType.EQ:
            result = self.visit(node.left).value == self.visit(node.right).value
        elif node.op.type == TokenType.NE:
            result = self.visit(node.left).value != self.visit(node.right).value
        elif node.op.type == TokenType.LT:
            result = self.visit(node.left).value < self.visit(node.right).value
        elif node.op.type == TokenType.LE:
            result = self.visit(node.left).value <= self.visit(node.right).value
        elif node.op.type == TokenType.AND:
            result = self.visit(node.left).value and self.visit(node.right).value
        elif node.op.type == TokenType.OR:
            result = self.visit(node.left).value or self.visit(node.right).value
        
        return Object.create(result)
        
    
    def visit_UnaryOp(self, node: UnaryOp):
        op = node.op.type
        if op == TokenType.ADD:
            result = +self.visit(node.expr).value
        elif op == TokenType.SUB:
            result = -self.visit(node.expr).value
        elif op == TokenType.NOT:
            result = not self.visit(node.expr).value
        
        return Object.create(result)

    def visit_IntObject(self, node: Object):
        return node
    
    def visit_FloatObject(self, node: Object):
        return node
    
    def visit_BoolObject(self, node: Object):
        return node

    def visit_StringObject(self, node: Object):
        return node

    def visit_ArrayObject(self, node: Object):
        return node
    
    def visit_DictionaryObject(self, node: Object):
        return node
    
    def visit_NoneObject(self, node: Object):
        return node
    
    def visit_RecordObject(self, node: Object):
        return node
    
    def visit_method(self, method):
        return method
    
    def visit_function(self, function):
        return function
    
    def visit_Compound(self, node: Compound):
        for child in node.children:
            if self.RETURN or self.BREAK or self.CONTINUE:
                break
            self.visit(child)

    def visit_NoOp(self, node: NoOp):
        pass
    
    def set_element(self, L, index, value):
        # function for recersively changing a object property
        i = index[0]
        target = self.visit(i.node)
        if len(index) < 2:
            if isinstance(i, ValueIndex):
                L[target] = value
            elif isinstance(i, PropertyIndex):
                L.properties[target] = value
        else:
            if isinstance(i, ValueIndex):
                L[target] = self.set_element(L[target], index[1:], value)
            elif isinstance(i, PropertyIndex):
                L.properties[target] = self.set_element(L[target], index[1:], value)
        return L
    
    def visit_Assign(self, node):
        var_name = node.left.value
        if var_name in self.current_scope.properties:
            val = self.visit_Var(node.left, traverse_lists=False)
            #print([self.visit(n) for n in node.left.indexes])
            if len(node.left.indexes) > 0:
                val = self.set_element(
                    val, 
                    node.left.indexes, 
                    self.visit(node.right)
                )
                return
        self.current_scope.insert(node.left, self.visit(node.right))

        #print("MEM:")
        #pprint(self.current_scope._variables)
    
    def visit_Var(self, node: Var, traverse_lists = True):
        var_name = node.value
        val = self.current_scope.get(node)
        #print(f"val type: {type(val)}")
        if traverse_lists:
            for i in node.indexes:
                target = i
                if isinstance(target, ValueIndex):
                    val = val[self.visit(target.node)]
                elif isinstance(target, PropertyIndex):
                    val = val.properties[self.visit(target.node)]
                else:
                    raise InterpreterError(f"Invalid index '{target}' of type {type(target)}")
                # when a StringObject is sliced a string is returned but we want a StringObject
                #print(type(val))
                if not isinstance(val, (Object,)):
                    val = Object.create(val)
                
                val = self.visit(val)
                #print(f"val type: {type(val)}")
        
        return val
    
    def visit_IndexedItem(self, node: IndexedItem):
        ret = node.node

        for index in node.indexes:
            if isinstance(index, ValueIndex):
                ret = Object.create(self.visit(ret)[self.visit(index.node)])
            if isinstance(index, PropertyIndex):
                ret = Object.create(self.visit(ret).properties[self.visit(index.node)])

        return ret
    
    def visit_Magic(self, node):
        if node.token.value == "OUTPUT":
            values = [str(self.visit(n)) for n in node.parameters]
            print(*values)
        elif node.token.value == "USERINPUT":
            return Object.create(input())
        elif node.token.value == "RETURN":
            values = [self.visit(n) for n in node.parameters]
            self.RETURN_VALUE = values[0] if len(values) > 0 else None
            self.RETURN = True
        elif node.token.value == "CONTINUE":
            self.CONTINUE = True
        elif node.token.value == "BREAK":
            self.BREAK = True
    
    def visit_SubroutineDefinition(self, node: SubroutineDefinition):
        s = deepcopy(node) # deepcopy is critical
        s.__class__ = Subroutine
        s.scopeBase = self.current_scope
        self.current_scope.insert(s.token, s)

    def visit_Subroutine(self, node: Subroutine):
        return node
        #print(f"{node.token.value}({', '.join([n.variable.value for n in node.parameters])})")
        #for c in node.children:
        #    print("  ", c)
    
    def visit_Record(self, node):
        self.current_scope.insert(node.token, node)

    def create_RecordObject(self, node: SubroutineCall, base: Record):
        record_object = RecordObject(base=base)

        for name, param in zip(base.parameters, node.parameters):
            value = self.visit(param.value)
            record_object.properties[name] = value

        return record_object

    def visit_SubroutineCall(self, node: SubroutineCall):
        #print(f"called {self.visit(node.subroutine_token)}({', '.join([str(n.value.value) for n in node.parameters])})")
        function = self.visit(node.subroutine_token) # the subroutine token is a SubroutineDefinition when it shouldn't be?

        if isinstance(function, Record):
            return self.create_RecordObject(node, function)
        
        elif isinstance(function, Subroutine):
            #node.subroutine_token.value
            old_scope = self.current_scope
            if function.scopeBase:
                #print(f"Switching to scope {function.scopeBase.name}")
                self.current_scope = function.scopeBase # move into functions module level scope
            
            function_scope = VariableScope("function_scope", self.current_scope)
            
            if function.classBase:
                function_scope.insert(Var(Token("this", TokenType.ID)), function.classBase)
            
            #print(function)
            if len(function.parameters) != len(node.parameters):
                raise InterpreterError("mismatched function parameters")
            for param_definition, parameter in zip(function.parameters, node.parameters):
                #print(self.visit(node.parameters[c].value))
                function_scope.insert(param_definition.variable, self.visit(parameter.value))

            self.current_scope = function_scope
            # execute function
            self.RETURN_VALUE = None
            self.RETURN = False
            self.visit(function.compound)
            self.RETURN = False
            result = self.RETURN_VALUE or NoneObject()
            self.RETURN_VALUE = None
            self.current_scope = self.current_scope.enclosing_scope

            #print(function_scope._variables)
            self.current_scope = old_scope # swap back scope
            return result
        
        elif isinstance(function, ClassDefinition):
            cls = function
            # need a variable pointing to the init function, this doesn't work
            s = SubroutineCall(None, node.parameters)
            #print("creating class instance...")
            return self.create_ClassInstance(s, cls)
        elif function is None:
            raise InterpreterError("subroutine is null!")
            print("ERROR, subroutine_token is none! ", node.subroutine_token, function, isinstance(node.subroutine_token, Subroutine))
            for prop in dir(node):
                print(f"-- {prop}: {getattr(node, prop)}")
        else:
            parameters = [self.visit(p.value) for p in node.parameters]
            return function(*parameters)
        
    def visit_IfStatement(self, node: IfStatement):
        if self.visit(node.condition).value:
            self.visit(node.consequence)
        else:
            for statement in node.alternatives:
                self.visit(statement)
    
    def visit_WhileStatement(self, node):
        while self.visit(node.condition).value:
            self.visit(node.consequence)
            if self.CONTINUE:
                self.CONTINUE = False
                continue
            if self.BREAK:
                self.BREAK = False
                break
    
    def visit_RepeatUntilStatement(self, node):
        while True:
            self.visit(node.consequence)

            if self.CONTINUE:
                self.CONTINUE = False
                continue
            if self.BREAK:
                self.BREAK = False
                break
            
            if self.visit(node.condition).value:
                break
    
    def visit_ForLoop(self, node: ForLoop):
        if node.to_step:
            step = self.visit(node.step).value if node.step else 1
            for i in range(self.visit(node.start).value, self.visit(node.end).value+1, step):
                self.current_scope.insert(node.variable, Object.create(i))
                self.visit(node.loop)
                if self.CONTINUE:
                    self.CONTINUE = False
                    continue
                if self.BREAK:
                    self.BREAK = False
                    break
        else:
            iterator = self.visit(node.iterator).value
            for i in iterator:
                current = i
                if isinstance(i, Object):
                    current = self.visit(i).value
                self.current_scope.insert(node.variable, Object.create(current))
                self.visit(node.loop)
                if self.CONTINUE:
                    self.CONTINUE = False
                    continue
                if self.BREAK:
                    self.BREAK = False
                    break
    
    def visit_TryCatch(self, node: TryCatch):
        try:
            self.visit(node.try_compound)
        except:
            self.visit(node.catch_compound)
    
    def visit_ClassDefinition(self, node: ClassDefinition):
        self.current_scope.insert(node.token, node)
        for v in node.static_values:
            node.properties[v.left.value] = self.visit(v.right)
        for f in node.subroutines:
            f.__class__ = Subroutine
            f.classBase = node
            node.properties[f.token.value] = f
        #print(node.properties)
        return node
    
    def create_ClassInstance(self, node: SubroutineCall, base: ClassDefinition):
        class_instance = ClassInstance(base=base)
        for name, func in class_instance.properties.items():
            if isinstance(func, Subroutine):
                func.classBase = class_instance

        initialise_function = class_instance.properties.get("INIT")
        if initialise_function:
            node.subroutine_token = initialise_function
            # something breaks with classes - need to fix
            self.visit(node)

        return class_instance
    
    def visit_Import(self, node: Import):
        #print(self.path)
        actual_location = self.visit(node.location).value
        actual_target = self.visit(node.target).value if node.target != None else None
        
        module_location = None
        isPython = False
        _break = False
        for loc in self.path.value:
            loc = loc.value
            for f in glob.glob(os.path.join(loc, "*.ecp")) + glob.glob(os.path.join(loc, "*.py")):
                if f.endswith(os.path.normpath(actual_location) + ".ecp"):
                    #print(f"found target at location {f}")
                    module_location = f
                    _break = True
                    break
                if f.endswith(os.path.normpath(actual_location) + ".py"):
                    module_location = f
                    _break = True
                    isPython = True
                    break
            if _break:
                break
        else:
            raise InterpreterError(f"module '{actual_location}' not found.")
        
        if not actual_target:
            actual_target = os.path.basename(actual_location)
        
        #print(f"import {actual_location} as {actual_target}")

        # need to be able to have variable scopes imported.
        # all the code from that scope has to access it's variables like it is the global scope
        # not sure how to do this...
        # this works.

        
        if isPython:
            spec = importlib.util.spec_from_file_location(actual_target, module_location)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules = {name: c for name, c in inspect.getmembers(module, inspect.isclass) if issubclass(c, BuiltinModule) and c != BuiltinModule and name == os.path.basename(actual_location)}
            for name, c in modules.items():
                v = Var(Token(actual_target, TokenType.ID))
                self.current_scope.insert(v, c(None))
        else:
            # doing the importing
            old_scope = self.current_scope
            if os.path.exists(module_location):
                with open(module_location) as f:
                    data = f.read()

                i = Interpreter(tracer=None, location=os.path.dirname(module_location), name=os.path.basename(module_location))
                i.interpret(Parser(Lexer().lexString(data)).parse())

                Interpreter.__interpreter__ = self
                i.current_scope.name = f"module:{actual_target}"
                self.current_scope.insert(Var(Token(actual_target, TokenType.ID)), i.current_scope)

            else:
                raise InterpreterError(f"module '{f}' not found.")


            self.current_scope = old_scope

    
    def interpret(self, parseTree: AST):
        tree = parseTree
        global_scope = VariableScope(f"global:{self.name}", None)
        self.current_scope = global_scope


        # register builtin functions
        for name, f in _BUILTINS(None).properties.items():
            v = Var(Token(name, TokenType.ID))
            self.current_scope.insert(v, f)
        # register builtin modules
        for c in BuiltinModule.__subclasses__():
            v = Var(Token(c.__name__[1:], TokenType.ID))
            self.current_scope.insert(v, c(None))
        # types
        for name, t in Object.types.items():
            v = Var(Token(name, TokenType.ID))
            self.current_scope.insert(v, t)
        
        self.visit(tree)
