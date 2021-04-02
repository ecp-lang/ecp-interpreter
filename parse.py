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



class AST:
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
            return token.value
        elif token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return token.value
        elif token.type == TokenType.ID:
            self.eat(TokenType.ID)
            return self.global_variables.variables[token.value]
        else:
            self.eat(TokenType.LPAREN)
            result = self.expr()
            self.eat(TokenType.RPAREN)
        return result

    
    def term(self):
        """term : factor (( MUL | DIV ) factor)* """
        result = self.factor()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
                result = result * self.factor()
            if token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
                result = result / self.factor()
        
        return result

    def assign(self):
        var = self.current_token
        self.eat(TokenType.ID)
        self.eat(TokenType.ASSIGN)
        result = self.expr()
        self.global_variables.variables[var.value] = result
        print(f"{var.value} -> {result}")
        return result
    
    def expr(self):
        """expr   :  term (( PLUS | MINUS ) term)*
                  |  var assign expr
        """
        if self.current_token.type == TokenType.ID:
            return self.assign()
        else:
            result = self.term()

            while self.current_token.type in (TokenType.ADD, TokenType.SUB):
                token = self.current_token
                if token.type == TokenType.ADD:
                    self.eat(TokenType.ADD)
                    result = result + self.term()
                elif token.type == TokenType.SUB:
                    self.eat(TokenType.SUB)
                    result = result - self.term()
            return result

    
    def parse(self):
        result = self.expr()
        print(result)