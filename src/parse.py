from lexer import *
import random
import math

"""
grammar

program               :  statement_list EOF

statement_list        :  (statement)*

statement             :  assignment_statement

assignment_statement  :  variable ASSIGN expr

magic_function        :  MAGIC expr (COMMA expr)*

if_statement          : IF condition THEN statement_list ( else_if_statement | else_statement )? ENDIF
else_if_statement     :  ELSE if_statement
else_statement        :  ELSE statement_list

for_loop              : FOR assignment_statement TO expr (STEP expr)? statement_list ENDFOR
                      | FOR variable IN expr statement_list ENDFOR

expr                  : relation
relation              : arithmetic_expr (rel_op arithmetic_expr)?
rel_op                : LESS_THAN
                      | GREATER_THAN
                      | EQUAL
                      | LESS_EQUAL
                      | GREATER_EQUAL
                      | NOT_EQUAL
arithmetic_expr       : term ((PLUS | MINUS) term)*
term                  : factor ((MUL | INT_DIV | DIV) factor)



factor                : PLUS factor
                      | MINUS factor
                      | INTEGER_CONST
                      | REAL_CONST
                      | LPAREN expr RPAREN
                      | TRUE
                      | FALSE
                      | variable
                      | function_call
                      | array

array                 : LS_PAREN (expr)? (COMMA expr)* RS_PAREN

variable              :  ID

assign                :  = | ←

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

class Bool(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Array(AST):
    def __init__(self, value):
        self.value = value
    
    def __setitem__(self, key, value):
        self.value[key] = value
    
    def __getitem__(self, key):
        return self.value[key]

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
        self.array_indexes = []

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

class SubroutineCall(AST):
    def __init__(self, subroutine_token, parameters):
        self.subroutine_token = subroutine_token
        self.parameters = parameters

class NoOp(AST):
    pass


class ParseError(Exception):
    pass

class InterpreterError(Exception):
    pass

class BuiltinSubroutineCall(AST):
    def __init__(self, subroutine_token, parameters):
        self.subroutine_token = subroutine_token
        self.parameters = parameters

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
            raise ParseError(f"Unexpected token: {self.current_token}")

    def eat_gap(self):
        while self.current_token.type in (TokenType.NEWLINE,):
            self.eat(self.current_token.type)


    @property
    def current_token(self):
        if self.token_num >= len(self.lexer.tokens):
            return Token(None, TokenType.EOF)
        return self.lexer.tokens[self.token_num]
    
    @property
    def next_token(self):
        if self.token_num + 1 >= len(self.lexer.tokens):
            return Token(None, TokenType.EOF)
        return self.lexer.tokens[self.token_num + 1]
    
    def error(self):
        raise ParseError(self.current_token)

    def program(self):
        
        return self.compound()
    
    def compound(self):
        nodes = self.statement_list()
        node = Compound()
        node.children = nodes

        return node
    
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
        elif self.current_token.type in (TokenType.BUILTIN_FUNCTION, TokenType.TYPE):
            node = self.builtin_function_call()
        elif self.current_token.type == TokenType.KEYWORD:
            node = self.process_keyword()
        elif self.current_token.type == TokenType.IF:
            node = self.if_statement()
            self.eat(TokenType.KEYWORD)
        elif self.current_token.type == TokenType.WHILE:
            node = self.while_statement()
            self.eat(TokenType.KEYWORD)
        elif self.current_token.type == TokenType.REPEAT:
            node = self.repeat_until_statement()
        elif self.current_token.type == TokenType.FOR:
            node = self.for_loop()
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
        while self.current_token.type == TokenType.LS_PAREN:
            self.eat(TokenType.LS_PAREN)
            node.array_indexes.append(self.expr())
            self.eat(TokenType.RS_PAREN)
        return node
    
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
            return node
        elif token.type == TokenType.SUB:
            self.eat(TokenType.SUB)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.NOT:
            self.eat(TokenType.NOT)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.INT:
            self.eat(TokenType.INT)
            return Num(token)
        elif token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return Num(token)
        elif token.type == TokenType.BOOLEAN:
            self.eat(TokenType.BOOLEAN)
            return Bool(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        elif token.type == TokenType.LS_PAREN:
            self.eat(TokenType.LS_PAREN)
            node = self.array()
            self.eat(TokenType.RS_PAREN)
            return node
        elif token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return String(token)
        elif token.type == TokenType.MAGIC:
            return self.magic_function()
        elif self.current_token.type in (TokenType.BUILTIN_FUNCTION, TokenType.TYPE):
            return self.builtin_function_call()
        else:
            node = self.variable()
            if self.current_token.type == TokenType.LPAREN:
                node = self.subroutine_call(node)
            return node

    
    def term(self):
        """term : factor (( MUL | DIV ) factor)* """
        node = self.actual_term()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.INT_DIV):
            token = self.current_token
            self.eat(token.type)
        
            node = BinOp(left=node, op=token, right=self.actual_term())
        
        return node
    
    def actual_term(self):
        node = self.factor()

        while self.current_token.type in (TokenType.POW, TokenType.MOD):
            token = self.current_token
            self.eat(token.type)
        
            node = BinOp(left=node, op=token, right=self.factor())
        
        return node
    
    def expr(self):
        return self.relation()

    def arithmetic_expr(self):
        """expr   :  term (( PLUS | MINUS ) term)*
        """
        node = self.term()

        while self.current_token.type in (
            TokenType.ADD, TokenType.SUB, 
            #TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE,
        ):
            token = self.current_token
            self.eat(token.type)
            
            node = BinOp(left=node, op=token, right=self.term())
        
        return node
    
    def relation(self):
        """
        relation : arithmetic_expr (rel_op arithmetic_expr)?
        rel_op   : LESS_THAN
                 | GREATER_THAN
                 | EQUAL
                 | LESS_EQUAL
                 | GREATER_EQUAL
                 | NOT_EQUAL
        """
        node = self.arithmetic_expr()
        if self.current_token.type in (
            TokenType.LT,
            TokenType.GT,
            TokenType.LE,
            TokenType.GE,
            TokenType.EQ,
            TokenType.NE,
            TokenType.AND, TokenType.OR
        ):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.arithmetic_expr())
        return node

    def magic_function(self):
        token = self.current_token
        self.eat(TokenType.MAGIC)
        if self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
        parameters = []
        if self.current_token.type not in (TokenType.EOF, TokenType.NEWLINE, TokenType.RPAREN):
            parameters.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.expr())
        if self.current_token.type == TokenType.RPAREN:
            self.eat(TokenType.RPAREN)
        node = Magic(token, parameters)

        return node
    
    def builtin_function_call(self):
        token = self.current_token
        self.eat(token.type) # TokenType.BUILTIN_FUNCTION or TokenType.TYPE
        self.eat(TokenType.LPAREN)

        parameters = []
        if self.current_token.type != TokenType.RPAREN:
            parameters.append(self.param())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.param())
        self.eat(TokenType.RPAREN)
        
        return BuiltinSubroutineCall(token, parameters)
    
    def declare_param(self):
        var = self.variable()
        node = DeclaredParam(var, None)
        token = self.current_token
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            self.eat(TokenType.TYPE)
        #if self.current_token.type == TokenType.ASSIGN:
        #    self.eat(TokenType.ASSIGN)
        #    right = self.expr()
        #    node.default = right
        
        return node
    
    def param(self):
        node = Param(self.expr(), None)
        return node

    
    def subroutine(self):
        self.eat(TokenType.KEYWORD)
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
        return Subroutine(token, parameters, compound)

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
        if token.value == "SUBROUTINE":
            node = self.subroutine()
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
            alternatives.extend(self.else_statement())
        
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
        return Array(values)
    
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
        if value != None:
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


class BuiltinFunctionContainer:
    def __init__(self, interpreter):
        self.interpreter = interpreter
    
    def USERINPUT(self, *args):
        return input(self.interpreter.visit(args[0].value) if len(args) > 0 else "")
    
    def LEN(self, *args):
        return len(self.interpreter.visit(args[0].value))
    
    def POSITION(self, s: Param, c: Param, *args):
        string = self.interpreter.visit(s.value)
        to_match = self.interpreter.visit(c.value)

        try:
            return string.index(to_match)
        except ValueError:
            return -1
    
    def SUBSTRING(self, start: Param, end: Param, string: Param, *args):
        start = self.interpreter.visit(start.value)
        end = self.interpreter.visit(end.value)
        string = self.interpreter.visit(string.value)

        return string[start:end+1]
    
    def STRING_TO_INT(self, string: Param):
        string = self.interpreter.visit(string.value)
        return int(string)
    
    def STRING_TO_REAL(self, string: Param):
        string = self.interpreter.visit(string.value)
        return float(string)
    
    def INT_TO_STRING(self, integer: Param):
        integer = self.interpreter.visit(integer.value)
        return str(integer)
    
    def REAL_TO_STRING(self, real: Param):
        real = self.interpreter.visit(real.value)
        return str(real)
    
    def CHAR_TO_CODE(self, char: Param):
        char = self.interpreter.visit(char.value)
        return ord(char)
    
    def CODE_TO_CHAR(self, code: Param):
        code = self.interpreter.visit(code.value)
        return chr(code)
    
    def RANDOM_INT(self, a: Param, b: Param):
        a = self.interpreter.visit(a.value)
        b = self.interpreter.visit(b.value)

        return random.randint(a, b)
    
    def SQRT(self, num: Param):
        num = self.interpreter.visit(num.value)
        return math.sqrt(num)
    
    def Int(self, other: Param):
        return int(self.interpreter.visit(other.value))
    
    def Real(self, other: Param):
        return float(self.interpreter.visit(other.value))
    
    def String(self, other: Param):
        return str(self.interpreter.visit(other.value))



class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser
        self.current_scope = None
        self.RETURN = False
        self.CONTINUE = False
        self.BREAK = False
        self.builtin_subroutines_container = BuiltinFunctionContainer(self)
    
    def visit_BinOp(self, node):
        if node.op.type == TokenType.ADD:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.SUB:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.type == TokenType.INT_DIV:
            return self.visit(node.left) // self.visit(node.right)
        elif node.op.type == TokenType.MOD:
            return self.visit(node.left) % self.visit(node.right)
        elif node.op.type == TokenType.POW:
            return self.visit(node.left) ** self.visit(node.right)
        
        elif node.op.type == TokenType.GT:
            return self.visit(node.left) > self.visit(node.right)
        elif node.op.type == TokenType.GE:
            return self.visit(node.left) >= self.visit(node.right)
        elif node.op.type == TokenType.EQ:
            return self.visit(node.left) == self.visit(node.right)
        elif node.op.type == TokenType.NE:
            return self.visit(node.left) != self.visit(node.right)
        elif node.op.type == TokenType.LT:
            return self.visit(node.left) < self.visit(node.right)
        elif node.op.type == TokenType.LE:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.op.type == TokenType.AND:
            return self.visit(node.left) and self.visit(node.right)
        elif node.op.type == TokenType.OR:
            return self.visit(node.left) or self.visit(node.right)
        
    
    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.ADD:
            return +self.visit(node.expr)
        elif op == TokenType.SUB:
            return -self.visit(node.expr)
        elif op == TokenType.NOT:
            return not self.visit(node.expr)

    def visit_Num(self, node):
        return node.value
    
    def visit_String(self, node):
        return node.value
    
    def visit_Bool(self, node):
        return node.value
    
    def visit_Array(self, node):
        return node.value
    
    def visit_Compound(self, node):
        for child in node.children:
            if self.RETURN or self.BREAK | self.CONTINUE:
                break
            self.visit(child)

    def visit_NoOp(self, node):
        pass

    def set_element(self, l, index, value):
        #print(f"list: {l}, indexes: {index}, value: {value}")
        if(len(index) == 1):
            l[self.visit(index[0])] = value
            #print(f"set {l}[{self.visit(index[0])}] to {value}")
        else:
            self.set_element(l[self.visit(index[0])],index[1:],value)
    
    def visit_Assign(self, node):
        var_name = node.left.value
        if var_name in self.current_scope._variables:
            val = self.visit_Var(node.left, traverse_lists=False)
            if isinstance(val, (list, str)) and len(node.left.array_indexes) > 0:
                self.set_element(
                    self.current_scope._variables[node.left.value], 
                    node.left.array_indexes, 
                    self.visit(node.right)
                )
                return
        self.current_scope.insert(node.left, self.visit(node.right))
    
    def visit_Var(self, node, traverse_lists = True):
        var_name = node.value
        val = self.current_scope.get(node)
        #print(f"val type: {type(val)}")
        if isinstance(val, (list, str)) and traverse_lists:
            for i in node.array_indexes:
                val = val[self.visit(i)]
                if isinstance(val, AST):
                    val = self.visit(val)
                #print(f"val type: {type(val)}")

        
                
        if var_name not in self.current_scope._variables:
            raise NameError(repr(var_name))
        else:
            return val
    
    def visit_Magic(self, node):
        if node.token.value == "OUTPUT":
            values = [self.visit(n) for n in node.parameters]
            print(*values)
        elif node.token.value == "RETURN":
            values = [self.visit(n) for n in node.parameters]
            self.RETURN_VALUE = values[0] if len(values) > 0 else None
            self.RETURN = True
        elif node.token.value == "CONTINUE":
            self.CONTINUE = True
        elif node.token.value == "BREAK":
            self.BREAK = True

    def visit_Subroutine(self, node):
        self.current_scope.insert(node.token, node)
        #print(f"{node.token.value}({', '.join([n.variable.value for n in node.parameters])})")
        #for c in node.children:
        #    print("  ", c)
    
    def visit_SubroutineCall(self, node):
        #print(f"called {node.subroutine_token.value}({', '.join([str(n.value.value) for n in node.parameters])})")
        function = self.current_scope.get(node.subroutine_token)
        
        function_scope = VariableScope(node.subroutine_token.value, self.current_scope)

        #print(function)
        if len(function.parameters) != len(node.parameters):
            raise InterpreterError("mismatched function parameters")
        for c, p in enumerate(function.parameters):
            function_scope.insert(p.variable, self.visit(node.parameters[c].value))
        
        self.current_scope = function_scope
        # execute function
        self.RETURN_VALUE = None
        self.RETURN = False
        self.visit(function.compound)
        self.RETURN = False
        result = self.RETURN_VALUE
        self.RETURN_VALUE = None
        self.current_scope = self.current_scope.enclosing_scope
        return result
    
    def visit_BuiltinSubroutineCall(self, node):
        func = getattr(self.builtin_subroutines_container, node.subroutine_token.value, None)
        if func:
            return func(*node.parameters)
        
    def visit_IfStatement(self, node):
        if self.visit(node.condition):
            self.visit(node.consequence)
        else:
            for statement in node.alternatives:
                self.visit(statement)
    
    def visit_WhileStatement(self, node):
        while self.visit(node.condition):
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
            
            if self.visit(node.condition):
                break
    
    def visit_ForLoop(self, node: ForLoop):
        if node.to_step:
            step = self.visit(node.step) if node.step else 1
            for i in range(self.visit(node.start), self.visit(node.end)+1, step):
                self.current_scope.insert(node.variable, i)
                self.visit(node.loop)
                if self.CONTINUE:
                    self.CONTINUE = False
                    continue
                if self.BREAK:
                    self.BREAK = False
                    break
        else:
            iterator = self.visit(node.iterator)
            for i in iterator:
                current = self.visit(i) if isinstance(i, AST) else i
                self.current_scope.insert(node.variable, current)
                self.visit(node.loop)
                if self.CONTINUE:
                    self.CONTINUE = False
                    continue
                if self.BREAK:
                    self.BREAK = False
                    break
    
    def interpret(self):
        tree = self.parser.parse()
        global_scope = VariableScope("global", None)
        self.current_scope = global_scope
        
        self.visit(tree)
