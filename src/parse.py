from lexer import *

"""
grammar for the maths expressions

expr   :  term (( PLUS | MINUS ) term)*
       |  var assign expr

term   :  factor (( MUL | DIV ) factor)*

factor :  (INTEGER | FLOAT | var) | LPAREN expr RPAREN

var    :  ID

assign :  = | ←

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
        self.global_variables = VariableContainer()
    
    
    def get_next_token(self):
        self.token_num += 1
        if self.token_num >= len(self.lexer.tokens):
            return Token(TokenType.EOF, None)
        return self.lexer.tokens[self.token_num]
    
    
    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.get_next_token()
        else:
            raise ParseError(f"{self.current_token.type} != {token_type}")

    
    @property
    def current_token(self):
        if self.token_num >= len(self.lexer.tokens):
            return Token(TokenType.EOF, None)
        return self.lexer.tokens[self.token_num]
    
    
    def factor(self):
        """factor : (INTEGER | FLOAT | var) | LPAREN expr RPAREN"""
        token = self.current_token
        if token.type == TokenType.INT:
            self.eat(TokenType.INT)
            return Num(token)
        elif token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return Num(token)
        #elif token.type == TokenType.ID:
        #    self.eat(TokenType.ID)
        #    return self.global_variables.variables[token.value]
        else:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
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

    #def assign(self):
    #    var = self.current_token
    #    self.eat(TokenType.ID)
    #    self.eat(TokenType.ASSIGN)
    #    result = self.expr()
    #    self.global_variables.variables[var.value] = result
    #    print(f"{var.value} -> {result}")
    #    return result
    
    def expr(self):
        """expr   :  term (( PLUS | MINUS ) term)*
                  |  var assign expr
        """
        if self.current_token.type == TokenType.ID:
            return
            #return self.assign()
        else:
            node = self.term()

            while self.current_token.type in (TokenType.ADD, TokenType.SUB):
                token = self.current_token
                if token.type == TokenType.ADD:
                    self.eat(TokenType.ADD)
                
                elif token.type == TokenType.SUB:
                    self.eat(TokenType.SUB)
                
                node = BinOp(left=node, op=token, right=self.term())
            
            return node

    
    def parse(self):
        return self.expr()

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
    
    def visit_BinOp(self, node):
        if node.op.type == TokenType.ADD:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.SUB:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            return self.visit(node.left) / self.visit(node.right)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)