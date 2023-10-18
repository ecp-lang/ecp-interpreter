from typing import *
from parsergen.lexer import *
from tabulate import tabulate
import codecs

def use_name(name, *rules):
    """Helper function for crating tokens which return their type as value
    
    Usage:
    >>> EQ = use_name("EQ", r"=")
    """
    def modifier(self, t):
        t.value = name
        return t
    
    modifier.__name__ = name

    return token(*rules)(modifier)

class EcpLexer(Lexer):
    # symbols
    ASSIGN  = r"←", r":="
    EQ      = use_name("EQ",      r"="           )
    ADD     = use_name("ADD",     r"\+"          )
    POW     = use_name("POW",     r"\*\*", r"POW")
    MUL     = use_name("MUL",     r"\*"          )
    SUB     = use_name("SUB",     r"\-",   r"–"  )
    INT_DIV = use_name("INT_DIV", r"DIV"         )
    MOD     = use_name("MOD",     r"%",    r"MOD")
    DIV     = use_name("DIV",     r"/"           )
    NE      = use_name("NE",      r"!=",   r"≠"  )
    LE      = use_name("LE",      r"<=",   r"≤"  )
    GE      = use_name("GE",      r">=",   r"≥"  )
    LT      = use_name("LT",      r"<"           )
    GT      = use_name("GT",      r">"           )
    NOT     = use_name("NOT",     r"NOT"         )
    OR      = use_name("OR",      r"OR"          )
    AND     = use_name("AND",     r"AND"         )
    
    @token(r"\n")
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        self.column = 0
        return None
    
    LPAREN = r"\("
    RPAREN = r"\)"
    LS_PAREN = r"\["
    RS_PAREN = r"\]"
    LC_BRACE = r"\{"
    RC_BRACE = r"\}"
    COMMA = r","
    COLON = r"\:"
    
    # types
    @token(r"(\d*\.\d+)", r"(\d+\.\d*)")
    def FLOAT(self, t):
        float(t.value)
        return t
    
    @token(r"\d+")
    def INT(self, t):
        int(t.value)
        return t
    
    BOOLEAN = r"True", r"False"

    @token(r"(\"|')")
    def STRING(self, t):
        end = t.value
        escape = False
        result = ""
        while True:
            if len(self.source) > 0:
                cur_char = self.source[0]
                self.step_source(1)
                if not escape and cur_char == "\\":
                    result += cur_char
                    if len(self.source) == 0:
                        continue
                    cur_char = self.source[0]
                    self.step_source(1)
                    escape = True
                if cur_char == end and not escape:
                    t.value = codecs.getdecoder("unicode_escape")(result)[0]
                    t.end = Pos(self.lineno, self.column)
                    return t
                result += cur_char
                escape = False
            else:
                raise Exception("No end of string")
    
    
    NONE = r"None"

    DOT = r"\."
    
    # keywords
    SUBROUTINE = r"SUBROUTINE",
    END = r"ENDSUBROUTINE", r"ENDIF", r"ENDWHILE", r"ENDFOR", r"ENDRECORD", r"ENDTRY", r"ENDCLASS", r"END"
    MAGIC = r"RETURN", r"CONTINUE", r"BREAK", r"OUTPUT", r"USERINPUT"
    IF = r"IF"
    THEN = r"THEN"
    ELSE = r"ELSE"
    WHILE = r"WHILE"
    REPEAT = r"REPEAT"
    UNTIL = r"UNTIL"
    FOR = r"FOR"
    TO = r"TO"
    IN = r"IN"
    STEP = r"STEP"
    RECORD = r"RECORD"
    CONSTANT = r"CONSTANT"
    TRY = r"TRY"
    CATCH = r"CATCH"
    CLASS = r"CLASS"
    IMPORT = r"IMPORT"
    AS = r"AS"

    ID = r"[a-zA-Z_][a-zA-Z0-9_]*"

    ignore = " \t"
    ignore_comment = r"#.*"