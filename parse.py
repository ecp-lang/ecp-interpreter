from lexer import *

class AST:
    pass




class Parser:
    def __init__(self, lexer: Lexer):
        self.nodes = {}
        self.offset = 0
        self.lexer = lexer
        self.token_num = 0
    
    def get_next_token(self):
        self.token_num += 1
        return self.lexer.tokens[self.token_num]
    
    @property
    def current_token(self):
        return self.lexer.tokens[self.token_num]
    
    
    def parse(self, tokens):
        pass
        #while self.token_num < len(self.lexer.tokens) - 1:
        #    token = self.current_token
        #    pass