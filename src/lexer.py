from tabulate import tabulate
from typing import *
from enum import Enum

class TokenType(Enum):
    ASSIGN = "ASSIGN"
    OPERATOR = "OPERATOR"
    
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    
    ID = "ID"
    NEWLINE = "NEWLINE"
    BRACKET = "BRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    KEYWORD = "KEYWORD"
    STRING_QUOTE = "STRING_QUOTE"
    MAGIC = "MAGIC"
    BOOLEAN = "BOOLEAN"
    COMMA = ","
    COLON = "COLON"
    TYPE = "TYPE"

    INVALID = "INVALID"
    EOF = "EOF"

    # types
    FLOAT = "FLOAT"
    INT = "INT"
    STRING = "STRING"

class Token:
    def __init__(self, value, type):
        self.value = value
        self.type = type
    
    def __str__(self):
        return f"<Token(value={self.value}, type={self.type})>"
    
    def __repr__(self):
        return self.__str__()

symbols = { # single char symbols
    "←":  TokenType.ASSIGN,
    "=":  TokenType.ASSIGN,
    "+":  TokenType.ADD,
    "*":  TokenType.MUL,
    "-":  TokenType.SUB,
    "/":  TokenType.DIV,
    "\n": TokenType.NEWLINE,
    "(":  TokenType.LPAREN,
    ")":  TokenType.RPAREN,
    "[":  TokenType.BRACKET,
    "]":  TokenType.BRACKET, 
    ",":  TokenType.COMMA,
    "\"": TokenType.STRING_QUOTE,
    ":":  TokenType.COLON
}
#symbols = [] # single-char keywords
other_symbols = {} # multi-char keywords
keywords = {
    "SUBROUTINE": TokenType.KEYWORD, 
    "ENDSUBROUTINE": TokenType.KEYWORD, 
    "RETURN": TokenType.MAGIC, 
    "WHILE": TokenType.KEYWORD, 
    "ENDWHILE": TokenType.KEYWORD,
    "OUTPUT": TokenType.MAGIC,
    "False": TokenType.BOOLEAN,
    "True": TokenType.BOOLEAN
}

types = {
    "Real": TokenType.TYPE,
    "Int": TokenType.TYPE,
    "Bool": TokenType.TYPE
}



KEYWORDS = {**symbols, **other_symbols, **keywords, **types}

class Lexer:
    def __init__(self):
        self.tokens: List[Token] = []
        self.lexme = ""
    
    def addToken(self, value, token_type, reset=True):
        token = Token(
            value = value,
            type = token_type
        )
        self.tokens.append(token)

        if reset:
            self.lexme = ""

    def lexString(self, string: str):
        if not string.endswith("\n"):
            string += "\n"
        self.tokens = []
        white_space = " "
        escape_character = "\\"
        self.lexme = ""
        is_string = False
        is_number = False
        prev_char = ""
        

        for i,char in enumerate(string):
            if char != white_space or is_string:
                self.lexme += char # adding a char each time
            if (i+1 < len(string)): # prevents error
                
                # Int and Real (float) processing
                if not is_string and char.isdigit() and not is_number:
                    is_number = True
                
                # string processing
                if char == "\"" and prev_char != "\\":
                    self.lexme = self.lexme[:-1]
                    is_string = not is_string
                    if not is_string:
                        self.addToken(self.lexme, TokenType.STRING)

                if (string[i+1] == white_space or string[i+1] in KEYWORDS.keys() or self.lexme in KEYWORDS.keys()) and not is_string: # if next char == ' '
                    if self.lexme != "":
                        if is_number:
                            try:
                                if self.lexme.count(".") == 1:
                                    self.addToken(
                                        float(self.lexme),
                                        TokenType.FLOAT,
                                    )
                                else:
                                    self.addToken(
                                        int(self.lexme),
                                        TokenType.INT,
                                    )
                            except ValueError:
                                self.addToken(
                                    self.lexme,
                                    TokenType.INVALID,
                                )
                        else:
                            if self.lexme in ("True", "False"):
                                self.addToken(
                                    bool(self.lexme),
                                    KEYWORDS.get(self.lexme, TokenType.ID),
                                )
                            else:
                                self.addToken(
                                    self.lexme,
                                    KEYWORDS.get(self.lexme, TokenType.ID),
                                )
                        is_number = False

        return self.tokens