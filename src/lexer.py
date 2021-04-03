from tabulate import tabulate
from typing import *
from enum import Enum

class TokenType(Enum):
    ASSIGN = "ASSIGN"
    OPERATOR = "OPERATOR"
    
    # operators
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    INT_DIV = "INT_DIV"

    LT = "LT"
    LE = "LE"
    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GE = "GE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    ID = "ID"
    NEWLINE = "NEWLINE"
    BRACKET = "BRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LS_PAREN = "LS_PAREN"
    RS_PAREN = "RS_PAREN"

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
    ARRAY = "ARRAY"
    BUILTIN_FUNCTION = "BUILTIN_FUNCTION"

    IF = "IF"
    ELSE = "ELSE"
    THEN = "THEN"

    WHILE = "WHILE"
    REPEAT = "REPEAT"
    UNTIL = "UNTIL"

class Token:
    def __init__(self, value, type, lineno=None, column=None):
        self.value = value
        self.type = type
        self.lineno = lineno
        self.column = column
    
    def __str__(self):
        return f"<Token(value={self.value}, type={self.type}, position={self.lineno}:{self.column})>"
    
    def __repr__(self):
        return self.__str__()

symbols = { # single char symbols
    "←":  TokenType.ASSIGN,
    ":=": TokenType.ASSIGN,
    "=":  TokenType.EQ,
    
    "+":  TokenType.ADD,
    "*":  TokenType.MUL,
    "-":  TokenType.SUB,
    "–":  TokenType.SUB,
    "DIV": TokenType.INT_DIV,
    "/":  TokenType.DIV,
    
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
    "<":  TokenType.LT,
    ">":  TokenType.GT,
    "≠":  TokenType.NE,
    "≤":  TokenType.LE,
    "≥":  TokenType.GE,
    "NOT": TokenType.NOT,
    "OR": TokenType.OR,
    "AND": TokenType.AND,
    
    "\n": TokenType.NEWLINE,
    "(":  TokenType.LPAREN,
    ")":  TokenType.RPAREN,
    "[":  TokenType.LS_PAREN,
    "]":  TokenType.RS_PAREN, 
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
    "USERINPUT": TokenType.BUILTIN_FUNCTION,
    "LEN": TokenType.BUILTIN_FUNCTION,
    "WHILE": TokenType.KEYWORD, 
    "ENDWHILE": TokenType.KEYWORD,
    "OUTPUT": TokenType.MAGIC,
    "False": TokenType.BOOLEAN,
    "True": TokenType.BOOLEAN,

    "IF": TokenType.IF,
    "THEN": TokenType.THEN,
    "ELSE": TokenType.ELSE,
    "ENDIF": TokenType.KEYWORD,

    "WHILE": TokenType.WHILE,
    "ENDWHILE": TokenType.KEYWORD,

    "REPEAT": TokenType.REPEAT,
    "UNTIL": TokenType.UNTIL,
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
        self.lineno = 0
        self.column = 0
    
    def addToken(self, value, token_type, reset=True):
        token = Token(
            value = value,
            type = token_type,
            lineno = self.lineno,
            column = self.column
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
        single_line_comment = False
        

        for i,char in enumerate(string):
            self.column += 1
            if char == "\n":
                self.lineno += 1
                self.column = 0
                single_line_comment = False
            if char != white_space or is_string:
                self.lexme += char # adding a char each time
            if char == "#" and prev_char != escape_character:
                single_line_comment = True
            if (i+1 < len(string)): # prevents error
                if single_line_comment:
                    self.lexme = ""
                    continue
                # Int and Real (float) processing
                if not is_string and char.isdigit() and not is_number:
                    is_number = True
                
                # string processing
                if char == "\"" and prev_char != escape_character:
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
                                    True if self.lexme == "True" else False,
                                    KEYWORDS.get(self.lexme, TokenType.ID),
                                )
                            else:
                                if string[i+1] in ("="):
                                    continue
                                self.addToken(
                                    self.lexme,
                                    KEYWORDS.get(self.lexme, TokenType.ID),
                                )
                        is_number = False

        return self.tokens
