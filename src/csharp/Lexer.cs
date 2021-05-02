using System.Collections.Generic;
using System.Collections;
using System.Linq;
using System;
namespace Ecp
{
    enum TokenType {
        ASSIGN,
        OPERATOR,
        ADD,
        SUB,
        MUL,
        DIV,
        INT_DIV,
        MOD,
        POW,

        LT,
        LE,
        EQ,
        NE,
        GT,
        GE,
        AND,
        OR,
        NOT,

        NEWLINE,
        BRACKET,
        LPAREN,
        RPAREN,
        LS_PAREN,
        RS_PAREN,
        STRING_QUOTE,
        BOOLEAN,
        COMMA,
        COLON,
        DOT,
        TYPE,
        INVALID,
        EOF,
        FLOAT,
        INT,
        STRING,
        ARRAY,
        BUILTIN_FUNCTION,
        SUBROUTINE,
        ID,
        KEYWORD,
        MAGIC,
        IF,
        ELSE,
        THEN,
        WHILE,
        REPEAT,
        UNTIL,
        FOR,
        TO,
        IN,
        STEP,
        CONSTANT,
        TRY,
        CATCH,
        CLASS,
        RECORD
    }
    class Token {
        public string value;
        public TokenType type;
        public int lineno, column;
        public Token(string value, TokenType _type, int lineno=0, int column=0){
            this.value = value;
            this.type = _type;
            this.lineno = lineno;
            this.column = column;
        }
        
        public override string ToString()
        {
            return $"<Token(value={this.value}, type={this.type}, position={this.lineno}:{this.column})>";
        }
        public string error_format(){
            return $"'{this.value}' ({this.type})";
        }
    }

    class Lexer {
        public static Dictionary<string, TokenType> keywords = new Dictionary<string, TokenType>{
            {"\u2190",  TokenType.ASSIGN},
            {":=", TokenType.ASSIGN},
            {"=",  TokenType.EQ},
            {"+",  TokenType.ADD},
            {"*",  TokenType.MUL},
            {"-",  TokenType.SUB},
            {"\u2013",  TokenType.SUB},
            {"DIV", TokenType.INT_DIV},
            {"MOD", TokenType.MOD},
            {"/",  TokenType.DIV},
            {"**", TokenType.POW},
            {"POW", TokenType.POW},
            {"!=", TokenType.NE},
            {"<=", TokenType.LE},
            {">=", TokenType.GE},
            {"<",  TokenType.LT},
            {">",  TokenType.GT},
            {"\u2260",  TokenType.NE},
            {"\u2264",  TokenType.LE},
            {"\u2265",  TokenType.GE},
            {"NOT", TokenType.NOT},
            {"OR", TokenType.OR},
            {"AND", TokenType.AND},
            {"\n", TokenType.NEWLINE},
            {"(",  TokenType.LPAREN},
            {")",  TokenType.RPAREN},
            {"[",  TokenType.LS_PAREN},
            {"]",  TokenType.RS_PAREN},
            {",",  TokenType.COMMA},
            {"'",  TokenType.STRING_QUOTE},
            {"\"", TokenType.STRING_QUOTE},
            {":",  TokenType.COLON},
            {".",  TokenType.DOT},
            {"SUBROUTINE", TokenType.SUBROUTINE},
            {"ENDSUBROUTINE", TokenType.KEYWORD},
            {"RETURN", TokenType.MAGIC},
            {"CONTINUE", TokenType.MAGIC},
            {"BREAK", TokenType.MAGIC},
            {"OUTPUT", TokenType.MAGIC},
            {"USERINPUT", TokenType.MAGIC},
            {"False", TokenType.BOOLEAN},
            {"True", TokenType.BOOLEAN},
            {"IF", TokenType.IF},
            {"THEN", TokenType.THEN},
            {"ELSE", TokenType.ELSE},
            {"ENDIF", TokenType.KEYWORD},
            {"WHILE", TokenType.WHILE},
            {"ENDWHILE", TokenType.KEYWORD},
            {"REPEAT", TokenType.REPEAT},
            {"UNTIL", TokenType.UNTIL},
            {"FOR", TokenType.FOR},
            {"TO", TokenType.TO},
            {"IN", TokenType.IN},
            {"STEP", TokenType.STEP},
            {"ENDFOR", TokenType.KEYWORD},
            {"RECORD", TokenType.RECORD},
            {"ENDRECORD", TokenType.KEYWORD},
            {"CONSTANT", TokenType.CONSTANT},
            {"TRY", TokenType.TRY},
            {"CATCH", TokenType.CATCH},
            {"ENDTRY", TokenType.KEYWORD},
            {"CLASS", TokenType.CLASS},
            {"ENDCLASS", TokenType.KEYWORD}
        };

        public List<Token> tokens = new List<Token>{};
        public string whitespaceChars = " \t\r";
        public string IdChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
        public string startIdChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_";
        public string numChars = "0123456789.";
        public Dictionary<string, string> escapeChars = new Dictionary<string, string>{
            {"n", "\n"},
            {"t", "\t"},
            {"\"", "\""},
            {"'", "'"}
        };

        public int lineno, column, curPos;
        public string source;
        public List<string> lines = new List<string>{};

        public Lexer(){
            this.init();
        }

        public void init(){
            this.lineno = 1;
            this.column = 0;
            this.curPos = 0;
            this.source = "";
            this.lines = new List<string>{};
            this.tokens = new List<Token>{};
        }

        public Token Token(string value, TokenType tokenType){
            return new Token(value, tokenType, lineno, column);
        }

        public bool reachedEnd {
            get {
                return curPos >= source.Length;
            }
        }

        public char curChar {
            get {
                if (curPos < source.Length) return source[curPos];
                return '\0'; // EOF
            }
        }

        public void ReachedEndError(){
            throw new System.Exception("Unexpected end of string");
        }

        void advance(){
            curPos += 1;
            column += 1;
        }
        
        char peek(){
            if (curPos + 1 >= source.Length) return '\0';
            return source[curPos+1];
        }
        
        void skipWhitespace(){
            while (whitespaceChars.Contains(curChar)){
                advance();
            }
        }
        
        void skipComment(){
            if (curChar == '#'){
                while (!"\0\n".Contains(curChar)){
                    advance();
                }
            }
        }
        
        Token id(){
            string s = "";
            while (IdChars.Contains(curChar)){
                s += curChar;
                advance();
            }

            if (keywords.Keys.Contains(s)) return Token(s, keywords[s]);
            
            return Token(s, TokenType.ID);
        }

        Token number(){
            string s = "";
            while (numChars.Contains(curChar)){
                s += curChar;
                advance();
            }
            
            try {
                if (s.Contains(".")){
                    float.Parse(s);
                    return Token(s, TokenType.FLOAT);
                }
                else {
                    int.Parse(s);
                    return Token(s, TokenType.INT);
                }
            }
            catch (System.FormatException){
                return Token(s, TokenType.INVALID);
            }
        }

        Token op(){
            string s = "";
            while (!whitespaceChars.Contains(curChar) && curChar != '\0'){
                s += curChar;
                advance();
                if (keywords.Keys.Contains(s) && !new List<string>{"=", "*"}.Contains(curChar.ToString())) break;
            }

            if (keywords.Keys.Contains(s)){
                return Token(s, keywords[s]);
            }
            return Token(s, TokenType.INVALID);
        }

        Token _string(){
            string s = "";
            char start = curChar;
            advance();
            while (curChar != start){
                if (curChar == '\\'){
                    advance();
                    if (escapeChars.Keys.Contains(curChar.ToString())){
                        s += escapeChars[curChar.ToString()];
                    }
                    else s += curChar;
                    advance();
                }
                else {
                    s += curChar;
                    advance();
                }
                if (reachedEnd) ReachedEndError();
            }
            advance();
            
            return Token(s, TokenType.STRING);
        }

        
        Token getToken(){
            if (curChar == '\n'){
                lineno += 1;
                column = 1;
                advance();
                return Token("\n", TokenType.NEWLINE);
            }
            else if (startIdChars.Contains(curChar)) return id();
            else if (numChars.Contains(curChar) && curChar != '.') return number();
            else if ("\"'".Contains(curChar)) return _string();
            else if (curChar == '\0') return Token("<EOF>", TokenType.EOF);
            else return op();
        }
            

        public List<Token> lexString(string source){
            init();
            this.source = source;
            lines = source.Split("\n").ToList();
            bool end = false;
            while (!end){
                skipWhitespace();
                skipComment();
                Token token = getToken();
                tokens.Add(token);
                if (token.type == TokenType.EOF) end = true;
            }
            return tokens;

        }
    }
}