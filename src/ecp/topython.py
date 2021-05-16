from .lexer import *
from .parse import TokenConversions, ParseError
import sys, os
from math import sqrt
from random import randint, uniform
from ast import *
import ast
_List = ast.List
_Dict = ast.Dict

TOKEN_TO_OP = {
    TokenType.ADD:     Add,
    TokenType.SUB:     Sub,
    TokenType.MUL:     Mult,
    TokenType.DIV:     Div,
    TokenType.INT_DIV: FloorDiv,
    TokenType.POW:     Pow,
    TokenType.MOD:     Mod,
    TokenType.LT:      Lt,
    TokenType.LE:      LtE,
    TokenType.EQ:      Eq,
    TokenType.NE:      NotEq,
    TokenType.GT:      Gt,
    TokenType.GE:      GtE,
    TokenType.AND:     And,
    TokenType.OR:      Or,
    TokenType.NOT:     Not,
}

def _dump(node, annotate_fields=True, include_attributes=False, *, indent=None):
    """
    Return a formatted dump of the tree in node.  This is mainly useful for
    debugging purposes.  If annotate_fields is true (by default),
    the returned string will show the names and the values for fields.
    If annotate_fields is false, the result string will be more compact by
    omitting unambiguous field names.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    include_attributes can be set to true.  If indent is a non-negative
    integer or string, then the tree will be pretty-printed with that indent
    level. None (the default) selects the single line representation.
    """
    def _format(node, level=0):
        if indent is not None:
            level += 1
            prefix = '\n' + indent * level
            sep = ',\n' + indent * level
        else:
            prefix = ''
            sep = ', '
        if isinstance(node, AST):
            cls = type(node)
            args = []
            allsimple = True
            keywords = annotate_fields
            for name in node._fields:
                try:
                    value = getattr(node, name)
                except AttributeError:
                    keywords = True
                    continue
                if value is None and getattr(cls, name, ...) is None:
                    keywords = True
                    continue
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                if keywords:
                    args.append('%s=%s' % (name, value))
                else:
                    args.append(value)
            if include_attributes and node._attributes:
                for name in node._attributes:
                    try:
                        value = getattr(node, name)
                    except AttributeError:
                        continue
                    if value is None and getattr(cls, name, ...) is None:
                        continue
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append('%s=%s' % (name, value))
            if allsimple and len(args) <= 3:
                return '%s(%s)' % (node.__class__.__name__, ', '.join(args)), not args
            return '%s(%s%s)' % (node.__class__.__name__, prefix, sep.join(args)), False
        elif isinstance(node, list):
            if not node:
                return '[]', True
            return '[%s%s]' % (prefix, sep.join(_format(x, level)[0] for x in node)), False
        return repr(node), True

    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    if indent is not None and not isinstance(indent, str):
        indent = ' ' * indent
    return _format(node)[0]


class ParseToPython:
    def __init__(self, lexer: LexerResult):
        self.result = None
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
        
        return Module(body=self.compound(), type_ignores=[])
    
    def compound(self):
        nodes = self.statement_list()
        #node = Module(body=nodes)
        if len(nodes) == 0:
            nodes.append(Pass(lineno=self.current_token.lineno, col_offset=self.current_token.lineno))
        return nodes
    
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
        if self.current_token.type == TokenType.MAGIC:
            node = self.magic_function()
        elif self.current_token.type == TokenType.IF:
            return self.if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.while_statement()
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
            value = self.expr()
            if isinstance(value, expr):
                return Expr(value=value, lineno=value.lineno, col_offset=value.col_offset)
            return value

        while self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN, TokenType.LPAREN):
            if self.current_token.type in (TokenType.DOT, TokenType.LS_PAREN):
                node = self.process_indexing(node)
            else:
                node = self.subroutine_call(node)
        
        return node
    
    def assignment_statement(self, var):
        left = var
        left.ctx = Store()
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.ID) # TYPE
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = Assign(targets=[left], value=right, lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        return node
    
    def variable(self):
        if self.current_token.type == TokenType.CONSTANT:
            self.eat(TokenType.CONSTANT)
        node = Name(id=self.current_token.value, ctx=Load(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        self.eat(TokenType.ID)
        return self.process_indexing(node)
    
    def process_indexing(self, node):
        while self.current_token.type in (TokenType.LS_PAREN, TokenType.DOT):
            if self.current_token.type == TokenType.LS_PAREN:
                self.eat(TokenType.LS_PAREN)
                node = Subscript(value=node, slice=Index(value=self.expr()), ctx=Load(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
                self.eat(TokenType.RS_PAREN)

            elif self.current_token.type == TokenType.DOT:
                self.eat(TokenType.DOT)
                node = Attribute(value=node, attr=self.id(), ctx=Load(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        return node
    
    def id(self):
        token = self.current_token
        self.eat(TokenType.ID)
        return token.value
    
    def empty(self):
        return Pass()
    
    def process_constant(self, t, value):
        if t == TokenType.INT:
            return Constant(value=int(value), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        elif t == TokenType.FLOAT:
            return Constant(value=float(value), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        elif t == TokenType.BOOLEAN:
            return Constant(value=(False if value.lower() == "false" else True), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        elif t == TokenType.STRING:
            return Constant(value=str(value), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)


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
            node = UnaryOp(op=UAdd(), operand=self.factor(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
            
        elif token.type == TokenType.SUB:
            self.eat(TokenType.SUB)
            node = UnaryOp(op=USub(), operand=self.factor(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        elif token.type == TokenType.NOT:
            self.eat(TokenType.NOT)
            node = UnaryOp(op=Not(), operand=self.factor(), lineno=self.current_token.lineno, col_offset=self.current_token.lineno)
        elif token.type in TokenConversions.keys():
            self.eat(token.type)
            node = self.process_constant(token.type, token.value)
        
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
        elif token.type in (TokenType.ID, TokenType.CONSTANT):
            node = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(node)
            elif self.current_token.type == TokenType.ASSIGN:
                node = self.assignment_statement(node)
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
        
            node = BinOp(left=node, op=TOKEN_TO_OP[token.type](), right=self.term(), lineno=token.lineno, col_offset=token.lineno)
        
        return node
    
    def term2(self):
        
        node = self.term()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.INT_DIV, TokenType.MOD):
            token = self.current_token
            self.eat(token.type)
        
            node = BinOp(left=node, op=TOKEN_TO_OP[token.type](), right=self.term(), lineno=token.lineno, col_offset=token.lineno)
        
        return node
    

    def term3(self):
        
        node = self.term2()

        while self.current_token.type in (
            TokenType.ADD, TokenType.SUB, 
            #TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE,
        ):
            token = self.current_token
            self.eat(token.type)
            
            node = BinOp(left=node, op=TOKEN_TO_OP[token.type](), right=self.term2(), lineno=token.lineno, col_offset=token.lineno)
        
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
            if not isinstance(node, Compare):
                node = Compare(left=node, ops=[TOKEN_TO_OP[token.type]()], comparators=[self.term3()], lineno=token.lineno, col_offset=token.lineno)
            else:
                node.ops.append(TOKEN_TO_OP[token.type]())
                node.comparators.append(self.term3())
        return node
    
    def term5(self):
        
        node = self.term4()
        while self.current_token.type in (
            TokenType.AND, TokenType.OR,
        ):
            token = self.current_token
            self.eat(token.type)
            if not isinstance(node, BoolOp):
                node = BoolOp(op=TOKEN_TO_OP[token.type](), values=[node, self.term4()], lineno=token.lineno, col_offset=token.lineno)
            else:
                node.values.append(self.term4())
        return node
        
    
    def expr(self):
        return self.term5()
        

    def magic_function(self):
        token = self.current_token
        self.eat(TokenType.MAGIC)
        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            p = self.param()
            if p is not None:
                parameters.append(p)
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                p = self.param()
                if p is not None:
                    parameters.append(p)
        
        if token.value == "RETURN":
            if len(parameters) == 1:
                return Return(value=parameters[0])
            if len(parameters > 1):
                return Return(value=Tuple(elts=parameters, ctx=Load()))
            return Return()
        elif token.value == "CONTINUE":
            return Continue()
        elif token.value == "BREAK":
            return Break()

        return Expr(value=Call(func=Name(id="_MAGIC_"+token.value, ctx=Load()), args=parameters, keywords=[]), lineno=token.lineno, col_offset=token.lineno)
    
    def declare_param(self):
        node = arg(arg=self.id())
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.ID) # TYPE
        #if self.current_token.type == TokenType.ASSIGN:
        #    self.eat(TokenType.ASSIGN)
        #    right = self.expr()
        #    node.default = right
        
        return node
    
    def param(self):
        return self.expr()

    
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
        self.eat(TokenType.END)
        return FunctionDef(
            name=token.value, 
            args=arguments(args=parameters, posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[]), 
            body=compound, 
            decorator_list=[], 
            returns=None, 
            type_comment=None, 
            lineno=token.lineno, 
            col_offset=token.lineno
        )

    def subroutine_call(self, var):
        token = self.current_token
        self.eat(TokenType.LPAREN)

        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            parameters.append(self.param())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.param())
        self.eat(TokenType.RPAREN)
        return Call(func=var, args=parameters, keywords=[], lineno=token.lineno, col_offset=token.lineno)
    
    def if_statement(self):
        token = self.current_token
        self.eat(TokenType.IF)

        condition = self.expr()
        self.eat_gap()
        self.eat(TokenType.THEN)

        consequence = self.compound()

        alternative = []
        if self.current_token.type == TokenType.ELSE and self.next_token.type == TokenType.IF:
            alternative = [self.elseif_statement()]
        elif self.current_token.type == TokenType.ELSE:
            alternative = self.else_statement()
        
        self.eat(TokenType.END)

        return If(test=condition, body=consequence, orelse=alternative, lineno=token.lineno, col_offset=token.lineno)

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
        self.eat(TokenType.END)

        return While(test=condition, body=consequence, orelse=[], lineno=token.lineno, col_offset=token.column)
        # TODO: implement else after while and for loops
    
    def repeat_until_statement(self):
        token = self.current_token
        self.eat(TokenType.REPEAT)
        
        consequence = self.compound()
        self.eat_gap()
        self.eat(TokenType.UNTIL)
        condition = self.expr()

        check = If(
            test=condition,
            body=[Break()],
            orelse=[]
        )

        node = While(test=Constant(value=True), body=consequence + [check], orelse=[], lineno=token.lineno, col_offset=token.column)

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
        return List(elts=values, ctx=Load())
    
    def dictionary(self):
        """ LC_BRACE ((expr COLON expr) (COMMA expr COLON expr)*)?  RC_BRACE """
        keys = []
        values = []
        if self.current_token.type != TokenType.RC_BRACE:
            self.eat_gap()
            keys.append(self.expr())
            self.eat(TokenType.COLON)
            self.eat_gap()
            values.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.eat_gap()
                self.eat(TokenType.COMMA)
                self.eat_gap()
                keys.append(self.expr())
                self.eat(TokenType.COLON)
                self.eat_gap()
                values.append(self.expr())
                self.eat_gap()
        return _Dict(keys=keys, values=values)
    
    def for_loop(self):
        """for_loop   : FOR ID ASSIGN expr TO expr (STEP expr)? statement_list ENDFOR
                      | FOR variable IN expr statement_list ENDFOR
        """
        loop = []
        self.eat(TokenType.FOR)
        variable = self.variable()
        variable.ctx = Store()
        if self.current_token.type == TokenType.ASSIGN:
            step = Constant(value=1)
            # FOR ID ASSIGN expr TO expr (STEP expr)? statement_list ENDFOR
            self.eat(TokenType.ASSIGN)
            start = self.expr()
            self.eat(TokenType.TO)
            end = self.expr()
            if self.current_token.type == TokenType.STEP:
                self.eat(TokenType.STEP)
                step = self.expr()
                
            self.eat_gap()
            body = self.compound()

            f = For(
                target=variable,
                iter=Call(
                    func=Name(id='range', ctx=Load()),
                    args=[
                      start,
                      BinOp(left=end, op=Add(), right=Constant(value=1)),
                      step
                    ],
                    keywords=[]
                ),
                body=body,
                orelse=[]
            )
            
        elif self.current_token.type == TokenType.IN:
            # FOR variable IN expr statement_list ENDFOR
            self.eat(TokenType.IN)
            iterator = self.expr()
            self.eat_gap()
            body = self.compound()
            
            f = For(
                target=variable,
                iter=iterator,
                body=body,
                orelse=[]
            )
        
        self.eat(TokenType.END)
        return f
    
    def record_definition(self):
        """record_definition  :  RECORD ID (variable)* ENDRECORD"""
        self.eat(TokenType.RECORD)
        token = self.id()
        self.eat_gap()
        parameters = []
        while self.current_token.type != TokenType.END:
            self.eat_gap()
            parameters.append(self.variable().id)
            if self.current_token.type == TokenType.COLON:
                self.eat(TokenType.COLON)
                self.eat(TokenType.ID) # TYPE
            self.eat_gap()
        
        self.eat_gap()
        self.eat(TokenType.END)
        # class something:
        #   def __init__(self, a, b, c, ...):
        #       self.a = a
        #       self.b = b
        #       self.c = c
        #       ...  = ...
        return ClassDef(
            name=token,
            bases=[],
            keywords=[],
            body=[
                FunctionDef(
                    name="__init__", 
                    args=arguments(args=[arg(arg='self')]+[arg(arg=p) for p in parameters], posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[]), 
                    body=[
                        Assign(
                            targets=[
                                Attribute(
                                    value=Name(
                                        id='self', 
                                        ctx=Load()
                                    ),
                                    attr=p,
                                    ctx=Store()
                                )
                            ],
                            value=Name(
                                id=p,
                                ctx=Load()
                            )
                        ) for p in parameters
                    ], 
                    decorator_list=[], 
                    returns=None, 
                    type_comment=None, 
                    lineno=self.current_token.lineno, 
                    col_offset=self.current_token.lineno
                )
            ],
            decorator_list=[],
            lineno=self.current_token.lineno,
            col_offset=self.current_token.column
        )
        
    
    def try_catch(self):
        self.eat(TokenType.TRY)
        try_compound = self.compound()
        self.eat(TokenType.CATCH)
        catch_compound = self.compound()
        self.eat(TokenType.END)

        return Try(
            body=try_compound,
            handlers=[
                ExceptHandler(
                    type=None,
                    name=None,
                    body=catch_compound
                )
            ],
            orelse=[],
            finalbody=[]
        )
    
    def class_definition(self):
        token = self.current_token
        self.eat(TokenType.CLASS)
        variable = self.variable()
        body = []
        self.eat_gap()
        body = self.compound()
        self.eat(TokenType.END)

        return ClassDef(
            name=variable.id,
            bases=[],
            keywords=[],
            body=body,
            decorator_list=[],
            lineno=token.lineno,
            col_offset=token.column
        )
    
    def import_statement(self):
        self.eat(TokenType.IMPORT)
        location = self.expr()
        target = Constant(value=None)
        if self.current_token.type == TokenType.AS:
            self.eat(TokenType.AS)
            target = self.expr()
        return Expr(
            value=Call(
                func=Name(id='_ECP_IMPORT', ctx=Load()),
                args=[location, target, Call(func=Name(id='globals', ctx=Load()), args=[], keywords=[])],
                keywords=[]
            )
        )

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error()

        return node


class Namespace:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def ecp(text: str=None, *, file: str=None, name="<unkown>", showAST=False, scope=None):
    if text is None:
        with open(file, encoding="utf-8") as f:
            text = f.read()
    if scope is None:
        scope = {}
    if isinstance(scope, Namespace):
        scope = vars(scope)
    scope.update(globals())
    r = fix_missing_locations(ParseToPython(Lexer().lexString(text)).parse())
    if showAST:
        print(_dump(r, indent=2))
    exec(compile(parse(r, mode="exec"), name, "exec"), scope)

    return Namespace(**scope)

def _ECP_IMPORT(location: str, target: str, scope=None):
    m = None
    for p in sys.path:
        if os.path.exists(p + location + ".ecp"):
            s = ecp(file=p + location + ".ecp", scope=globals())
            scope[target] = s
            return
    raise ImportError(name=location, path=p + location + ".ecp")


# ECP BUILTINS

_MAGIC_OUTPUT = print
_MAGIC_USERINPUT = input
INPUT = input
LEN = len
Integer = int
Int = int
Real = float
Bool = bool
String = str
Array = list
Dictionary = dict

def POSITION(string: str, to_match: str) -> int:
    try:
        return string.index(to_match)
    except:
        return -1

def SUBSTRING(start: int, end: int, string: str):
    return string[start:end+1]

STRING_TO_INT = int
STRING_TO_REAL = float
INT_TO_STRING = REAL_TO_STRING = str
CHAR_TO_CODE = ord
CODE_TO_CHAR = chr
RANDOM_INT = randint
SQRT = sqrt

PY = exec