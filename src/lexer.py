from tabulate import tabulate
from typing import *
from enum import Enum
import string

class TokenType(Enum):
    ASSIGN = "ASSIGN"
    OPERATOR = "OPERATOR"
    
    # operators
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    INT_DIV = "INT_DIV"
    MOD = "MOD"
    POW = "POW"

    LT = "LT"
    LE = "LE"
    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GE = "GE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    NEWLINE = "NEWLINE"
    BRACKET = "BRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LS_PAREN = "LS_PAREN"
    RS_PAREN = "RS_PAREN"
    LC_BRACE = "LC_BRACE"
    RC_BRACE = "RC_BRACE"

    STRING_QUOTE = "STRING_QUOTE"
    BOOLEAN = "BOOLEAN"
    COMMA = "COMMA"
    COLON = "COLON"
    DOT = "DOT"
    TYPE = "TYPE"

    INVALID = "INVALID"
    EOF = "EOF"

    # types
    FLOAT = "FLOAT"
    INT = "INT"
    STRING = "STRING"
    ARRAY = "ARRAY"
    BUILTIN_FUNCTION = "BUILTIN_FUNCTION"
    SUBROUTINE = "SUBROUTINE"

    ID = "ID"
    KEYWORD = "KEYWORD"
    MAGIC = "MAGIC"
    IF = "IF"
    ELSE = "ELSE"
    THEN = "THEN"

    WHILE = "WHILE"
    REPEAT = "REPEAT"
    UNTIL = "UNTIL"
    FOR = "FOR"
    TO = "TO"
    IN = "IN"
    STEP = "STEP"
    CONSTANT = "CONSTANT"
    TRY = "TRY"
    CATCH = "CATCH"
    CLASS = "CLASS"
    RECORD = "RECORD"

class Token:
    def __init__(self, value, _type, lineno=0, column=0):
        self.value = value
        self.type = _type
        self.lineno = lineno
        self.column = column
    
    def __str__(self):
        return f"<Token(value={self.value}, type={self.type}, position={self.lineno}:{self.column})>"
    
    def __repr__(self):
        return self.__str__()
    
    def error_format(self):
        return f"'{self.value}' ({self.type})"
    
    @property
    def pos(self):
        return self.lineno, self.column

symbols = { # single char symbols
    "\u2190":  TokenType.ASSIGN,
    ":=": TokenType.ASSIGN,
    "=":  TokenType.EQ,
    
    "+":  TokenType.ADD,
    "*":  TokenType.MUL,
    "-":  TokenType.SUB,
    "\u2013":  TokenType.SUB,
    "DIV": TokenType.INT_DIV,
    "MOD": TokenType.MOD,
    "/":  TokenType.DIV,
    "**": TokenType.POW,
    "POW": TokenType.POW,
    
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
    "<":  TokenType.LT,
    ">":  TokenType.GT,
    "\u2260":  TokenType.NE,
    "\u2264":  TokenType.LE,
    "\u2265":  TokenType.GE,
    "NOT": TokenType.NOT,
    "OR": TokenType.OR,
    "AND": TokenType.AND,
    
    "\n": TokenType.NEWLINE,
    "(":  TokenType.LPAREN,
    ")":  TokenType.RPAREN,
    "[":  TokenType.LS_PAREN,
    "]":  TokenType.RS_PAREN, 
    "{":  TokenType.LC_BRACE,
    "}":  TokenType.RC_BRACE,
    ",":  TokenType.COMMA,
    "'":  TokenType.STRING_QUOTE,
    "\"": TokenType.STRING_QUOTE,
    ":":  TokenType.COLON,
    ".":  TokenType.DOT,
}
QUOTE_CHARS = ("'", "\"")
#symbols = [] # single-char keywords
other_symbols = {} # multi-char keywords
builtin_functions = [
    #"USERINPUT", "LEN", "POSITION", "SUBSTRING", 
    #"STRING_TO_INT", "STRING_TO_REAL", "INT_TO_STRING", 
    #"REAL_TO_STRING", "CHAR_TO_CODE", "CODE_TO_CHAR", "RANDOM_INT",
    #"SQRT",
]
keywords = {
    "SUBROUTINE": TokenType.SUBROUTINE, 
    "ENDSUBROUTINE": TokenType.KEYWORD, 
    "RETURN": TokenType.MAGIC,
    "CONTINUE": TokenType.MAGIC,
    "BREAK": TokenType.MAGIC,
    "OUTPUT": TokenType.MAGIC,
    "USERINPUT": TokenType.MAGIC,
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

    "FOR": TokenType.FOR,
    "TO": TokenType.TO,
    "IN": TokenType.IN,
    "STEP": TokenType.STEP,
    "ENDFOR": TokenType.KEYWORD,
    
    "RECORD": TokenType.RECORD,
    "ENDRECORD": TokenType.KEYWORD,
    "CONSTANT": TokenType.CONSTANT,
    "TRY": TokenType.TRY,
    "CATCH": TokenType.CATCH,
    "ENDTRY": TokenType.KEYWORD,
    "CLASS": TokenType.CLASS,
    "ENDCLASS": TokenType.KEYWORD,
}

types = {
    #"Real": TokenType.TYPE,
    #"Integer": TokenType.TYPE,
    #"Int": TokenType.TYPE,
    #"Bool": TokenType.TYPE,
    #"String": TokenType.TYPE,
    #"Array": TokenType.TYPE,
    #"Record": TokenType.TYPE,
}



KEYWORDS = {**symbols, **other_symbols, **keywords}

class Lexer:
    def __init__(self):
        self.tokens: List[Token] = []
        self.whitespaceChars = " \t\r"

        self.IdChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        self.startIdChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
        self.numChars = "0123456789."
        self.escapeChars = {
            "n": "\n",
            "t": "\t",
            "\"": "\"",
            "'": "'"
        }

        self.init()
    
    def init(self):
        self.lineno = 1
        self.column = 0
        self.curPos = 0
        self.source = ""
        self.lines = []
        self.tokens = []
    
    def Token(self, value, tokenType):
        token = Token(
            value, tokenType,
            lineno=self.lineno, column=self.column
        )
        return token
    
    @property
    def reachedEnd(self):
        return self.curPos >= len(self.source)

    @property
    def curChar(self):
        if self.curPos < len(self.source):
            return self.source[self.curPos]
        else:
            return "\0" # EOF
    
    def ReachedEndError(self):
        raise Exception("Unexpected end of string")

    def advance(self):
        self.curPos += 1
        self.column += 1
    
    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return "\0"
        return self.source[self.curPos+1]
    
    def skipWhitespace(self):
        while self.curChar in self.whitespaceChars:
            self.advance()
    
    def skipComment(self):
        if self.curChar == "#":
            while self.curChar not in "\0\n":
                self.advance()
    
    def id(self):
        s = ""
        while self.curChar in self.IdChars:
            s += self.curChar
            self.advance()

        if s in KEYWORDS.keys():
            return self.Token(s, KEYWORDS[s])
        else:
            return self.Token(s, TokenType.ID)

    def number(self):
        s = ""
        while self.curChar in self.numChars:
            s += self.curChar
            self.advance()
        
        try:
            if "." in s:
                float(s)
                return self.Token(s, TokenType.FLOAT)
            else:
                int(s)
                return self.Token(s, TokenType.INT)
        except ValueError:
            return self.Token(s, TokenType.INVALID)

    def op(self):
        s = ""
        while self.curChar not in self.whitespaceChars + "\0":
            s += self.curChar
            self.advance()

            if s in KEYWORDS.keys() and self.curChar not in ("=", "*"):
                break

        if s in KEYWORDS.keys():
            return self.Token(s, KEYWORDS[s])
        else:
            return self.Token(s, TokenType.INVALID)

    def _string(self):
        s = ""
        start = self.curChar
        self.advance()
        while self.curChar != start:
            if self.curChar == "\\":
                self.advance()
                if self.curChar in self.escapeChars.keys():
                    s += self.escapeChars[self.curChar]
                else:
                    s += self.curChar
                self.advance()
            else:
                s += self.curChar
                self.advance()
            
            if self.reachedEnd:
                self.ReachedEndError()
        
        self.advance()
        
        return self.Token(s, TokenType.STRING)

    
    def getToken(self):
        if self.curChar == "\n":
            self.lineno += 1
            self.column = 0
            self.advance()
            return Token("\n", TokenType.NEWLINE)
        elif self.curChar in self.startIdChars: # ID
            return self.id()
        elif self.curChar in self.numChars and self.curChar != ".":
            return self.number()
        elif self.curChar in "\"'":
            return self._string()
        elif self.curChar == "\0":
            return self.Token("<EOF>", TokenType.EOF)
        else:
            return self.op()
        

    def lexString(self, source):
        self.init()
        self.source = source
        self.lines = source.split("\n")
        end = False
        while not end:
            self.skipWhitespace()
            self.skipComment()
            token = self.getToken()
            self.tokens.append(token)
            if token.type == TokenType.EOF:
                end = True
        return self.tokens
