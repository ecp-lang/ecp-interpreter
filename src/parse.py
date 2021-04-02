from lexer import *
from collections import OrderedDict

"""
grammar

program  :  statement_list EOF

statement_list  :  (statement)*

statement  :  assignment_statement

assignment_statement  :  variable ASSIGN expr

magic_function  :  MAGIC expr (COMMA expr)*

expr  :  term (( PLUS | MINUS ) term)*

term  :  factor (( MUL | DIV ) factor)*

factor  : PLUS factor
        | MINUS factor
        | INTEGER
        | FLOAT
        | LPAREN expr RPAREN
        | variable

variable  :  ID

assign  :  = | ←

"""



class AST(object):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


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

class SubroutineCall(AST):
    def __init__(self, subroutine_token, parameters):
        self.subroutine_token = subroutine_token
        self.parameters = parameters

class NoOp(AST):
    pass


class ParseError(Exception):
    pass


class VariableContainer:
    def __init__(self):
        self.variables = {}


class Parser:
    def __init__(self, lexer: Lexer):
        self.nodes = {}
        self.offset = 0
        self.lexer = lexer
        self.token_num = 0
    
    
    def get_next_token(self):
        self.token_num += 1
        if self.token_num >= len(self.lexer.tokens):
            return Token(None, TokenType.EOF)
        return self.lexer.tokens[self.token_num]
    
    
    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.get_next_token()
        else:
            raise ParseError(f"{self.current_token.type} != {token_type}")

    
    @property
    def current_token(self):
        if self.token_num >= len(self.lexer.tokens):
            return Token(None, TokenType.EOF)
        return self.lexer.tokens[self.token_num]
    
    def error(self):
        raise ParseError(self.current_token)

    def program(self):
        
        nodes = self.statement_list()
        
        root = Compound()
        for node in nodes:
            root.children.append(node)

        return root
    
    def statement_list(self):
        node = self.statement()

        results = [node]

        while self.current_token.type == TokenType.NEWLINE:
            self.eat(TokenType.NEWLINE)
            results.append(self.statement())

        if self.current_token.type == TokenType.ID:
            self.error()

        return results
    
    def statement(self):
        if self.current_token.type == TokenType.ID:
            var = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(var)
            else:
                node = self.assignment_statement(var)
        elif self.current_token.type == TokenType.MAGIC:
            node = self.magic_function()
        elif self.current_token.type == TokenType.KEYWORD:
            node = self.process_keyword()
        else:
            node = self.empty()
        return node
    
    def assignment_statement(self, var):
        left = var
        token = self.current_token
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.TYPE)
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = Assign(left, token, right)
        return node
    
    def variable(self):
        node = Var(self.current_token)
        self.eat(TokenType.ID)
        return node
    
    def empty(self):
        return NoOp()

    def factor(self):
        """factor : PLUS  factor
              | MINUS factor
              | INTEGER
              | FLOAT
              | STRING
              | LPAREN expr RPAREN
              | variable
              | function_call
        """
        token = self.current_token
        if token.type == TokenType.ADD:
            self.eat(TokenType.ADD)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.SUB:
            self.eat(TokenType.SUB)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.INT:
            self.eat(TokenType.INT)
            return Num(token)
        elif token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return Num(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        elif token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return String(token)
        else:
            node = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(node)
            return node

    
    def term(self):
        """term : factor (( MUL | DIV ) factor)* """
        node = self.factor()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
        
            node = BinOp(left=node, op=token, right=self.factor())
        
        return node
    
    def expr(self):
        """expr   :  term (( PLUS | MINUS ) term)*
        """
        node = self.term()

        while self.current_token.type in (TokenType.ADD, TokenType.SUB):
            token = self.current_token
            if token.type == TokenType.ADD:
                self.eat(TokenType.ADD)
            
            elif token.type == TokenType.SUB:
                self.eat(TokenType.SUB)
            
            node = BinOp(left=node, op=token, right=self.term())
        
        return node

    def magic_function(self):
        token = self.current_token
        self.eat(TokenType.MAGIC)
        parameters = [self.expr()]
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
            self.eat(TokenType.TYPE)
        if self.current_token.type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            right = self.expr()
            node.default = right
        
        return node
    
    def param(self):
        if self.current_token.type == TokenType.ID:
            pass
        else:
            node = Param(self.expr(), None)
            return node

    
    def subroutine(self):
        self.eat(TokenType.KEYWORD)
        token = self.current_token
        self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)
        parameters = [self.declare_param()]
        
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            parameters.append(self.declare_param())
        self.eat(TokenType.RPAREN)
        compound = Compound()
        compound.children = self.statement_list()
        self.eat(TokenType.KEYWORD)
        return Subroutine(token, parameters, compound)

    def subroutine_call(self, var):
        self.eat(TokenType.LPAREN)

        parameters = [self.param()]

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            parameters.append(self.param())
        self.eat(TokenType.RPAREN)

        return SubroutineCall(var, parameters)

    def process_keyword(self):
        token = self.current_token
        if token.value == "SUBROUTINE":
            node = self.subroutine()
        else:
            node = self.empty()
        return node

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error()

        return node


class VariableScope(object):
    def __init__(self, name, enclosing_scope):
        self.name = name
        self.enclosing_scope = enclosing_scope
        self._variables = {}
    
    def insert(self, var, value):
        self._variables[var.value] = value
    
    def get(self, var):
        value = self._variables.get(var.value)
        if value:
            return value
        
        if value is None:
            while self.enclosing_scope != None:
                return self.enclosing_scope.get(var)
        
        raise NameError(f"{var.value} does not exist")

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))




class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser
        self.current_scope = None
    
    def visit_BinOp(self, node):
        if node.op.type == TokenType.ADD:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.SUB:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            return self.visit(node.left) / self.visit(node.right)
    
    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.ADD:
            return +self.visit(node.expr)
        elif op == TokenType.SUB:
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value
    
    def visit_String(self, node):
        return node.value
    
    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        pass
    
    def visit_Assign(self, node):
        var_name = node.left.value
        self.current_scope.insert(node.left, self.visit(node.right))
    
    def visit_Var(self, node):
        var_name = node.value
        val = self.current_scope.get(node)
        if val is None:
            raise NameError(repr(var_name))
        else:
            return val
    
    def visit_Magic(self, node):
        if node.token.value == "OUTPUT":
            print(*[self.visit(n) for n in node.parameters])
        elif node.token.value == "RETURN":
            self.RETURN_VALUE = [self.visit(n) for n in node.parameters][0]

    def visit_Subroutine(self, node):
        self.current_scope.insert(node.token, node)
        #print(f"{node.token.value}({', '.join([n.variable.value for n in node.parameters])})")
        #for c in node.children:
        #    print("  ", c)
    
    def visit_SubroutineCall(self, node):
        #print(f"called {node.subroutine_token.value}({', '.join([str(n.value.value) for n in node.parameters])})")
        function_scope = VariableScope(node.subroutine_token.value, self.current_scope)

        function = self.current_scope.get(node.subroutine_token)
        #print(function)
        for c, p in enumerate(function.parameters):
            function_scope.insert(p.variable, node.parameters[c].value.value)
        
        self.current_scope = function_scope

        # execute function
        self.RETURN_VALUE = None
        self.visit(function.compound)
        result = self.RETURN_VALUE
        self.RETURN_VALUE = None
        self.current_scope = self.current_scope.enclosing_scope

        return result
    
    def interpret(self):
        tree = self.parser.parse()
        global_scope = VariableScope("global", None)
        self.current_scope = global_scope
        
        self.visit(tree)
