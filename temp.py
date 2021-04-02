from enum import Enum
class TokenType(Enum):
    ASSIGN     = "="
    PLUS       = "+"
    MINUS      = "-"
    #NEWLINE   = "\n"
    LPAREN     = "("
    RPAREN     = ")"
    COMMA      = ","
    DOT        = "."
    QUOTE      = "\""

    # reserved keywords
    OUTPUT     = "OUTPUT"

    # misc
    ID         = "ID"
    ESCAPE     = "\""
    INT_CONST  = "INT_CONST"
    REAL_CONST = "REAL_CONST"

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __str__(self):
        return f"Token(type={self.type}, value={self.value})"
    def __repr__(self):
        return self.__str__()

