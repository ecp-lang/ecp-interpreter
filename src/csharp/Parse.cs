using System.Collections.Generic;
using System.Reflection;
using System.Collections;
using System.Linq;
using System;
namespace Ecp
{
    class AST {
        public virtual string Repr(){
            return "<ast node>";
        }
    }
    
    class BinOp : AST {
        public AST left, right;
        public Token op, token;
        public BinOp(AST left, Token op, AST right){
            this.left = left;
            this.token = this.op = op;
            this.right = right;
        }
    }
    class UnaryOp : AST {
        public Token op, token;
        public AST expr;
        public UnaryOp(Token op, AST expr){
            this.token = this.op = op;
            this.expr = expr;
        }
    }

    class Compound : AST {
        public List<AST> children;
        public Compound(){
            children = new List<AST>{};
        }
    }

    class Assign : AST {
        public AST left, right;
        public Token op, token;
        public Assign(AST left, Token op, AST right){
            this.left = left;
            this.token = this.op = op;
            this.right = right;
        }
    }
    class Var : AST {
        public Token token;
        public object value;
        public List<object> array_indexes;
        public Var(Token token){
            this.token = token;
            this.value = token.value;
            array_indexes = new List<object>{};
        }
    }

    class Magic : AST {
        public Token token;
        public List<AST> parameters;
        public Magic (Token token, List<AST> parameters){
            this.token = token;
            this.parameters = parameters;
        }
    }
    class DeclaredParam : AST {
        public Var variable;
        public AST defaultValue;
        public DeclaredParam(Var variable, AST defaultValue){
            this.variable = variable;
            this.defaultValue = defaultValue;
        }
    }

    class Param : AST {
        public AST value, id;
        public Param(AST value, AST id){
            this.value = value;
            this.id = id;
        }
    }

    class Subroutine : AST {
        public Token token;
        public List<DeclaredParam> parameters;
        public Compound compound;
        public bool builtin;
        public object classBase; // NOTE: ClassObject not done yet!
        public Subroutine(Token token, List<DeclaredParam> parameters, Compound compound){
            this.token = token;
            this.parameters = parameters;
            this.compound = compound;
            this.builtin = false;
            this.classBase = null;
        }
    }

    class SubroutineCall : AST {
        public Var subroutine_token;
        public List<Param> parameters;
        public SubroutineCall(Var subroutine_token, List<Param> parameters){
            this.subroutine_token = subroutine_token;
            this.parameters = parameters;
        }
    }

    class NoOp : AST {}

    class Object : AST {
        public static Dictionary<TokenType, Type> TypeConversions = new Dictionary<TokenType, Type>{
            {TokenType.INT, typeof(System.Int64)},
            {TokenType.FLOAT, typeof(System.Double)},
            {TokenType.BOOLEAN, typeof(System.Boolean)},
            {TokenType.STRING, typeof(System.String)}
        };
        public dynamic value;
        public Dictionary<object, object> properties;
        public Object(){}
        public Object(object value){
            this.initialize(value);
        }

        public void initialize(object value){
            this.value = value;
            this.properties = new Dictionary<object, object>{};
        }

        public static T convert<T>(object value){
            if (value is Object){
                return (T)Convert.ChangeType(
                    ((Object)value).value, 
                    typeof(T)
                );
            }
            else {
                return (T)Convert.ChangeType(
                    value, 
                    typeof(T)
                );
            }
        }

        public static Object create(object value){
            switch (value.GetType().ToString()){
                case "System.Int16":
                case "System.Int32":
                case "System.Int64":
                    return new IntObject(value);
                case "System.Single":
                case "System.Double":
                    return new FloatObject(value);
                case "Sytem.Boolean":
                    return new BoolObject(value);
                case "System.String":
                    return new StringObject(value);
                case "System.Collections.Generic.List`1[System.Object]":
                    return new ArrayObject(value);
            }
            return new Object(value);
        }

        public static Object create(object value, TokenType tokenType){
            Type convertTo = TypeConversions[tokenType];
            value = Convert.ChangeType(value, convertTo);
            return create(value);
        }

        public static Object operator +(Object a){
            return create(a.value);
        }
        public static Object operator -(Object a){
            return create(-a.value);
        }
        public static Object operator +(Object a, Object b){
            return create(a.value + b.value);
        }
        public static Object operator -(Object a, Object b){
            return create(a.value - b.value);
        }
        public static Object operator *(Object a, Object b){
            return create((dynamic)a.value * (dynamic)b.value);
        }
        public static Object operator /(Object a, Object b){
            return create((dynamic)a.value / (dynamic)b.value);
        }

        public object this[object index]
        {
            get {
                if (index is Object) index = ((Object)index).value;
                if (index is int) return this.value[(int)index];
                return this.value[(string)index];
            }
            set {
                if (index is Object) index = ((Object)index).value;
                if (index is int) this.value[(int)index] = value;
                if (index is string) this.value[(string)index] = value;
            }
        }

        public override string ToString()
        {
            return this.value.ToString();
        }

        public override string Repr(){
            return ToString();
        }
    }

    class IntObject : Object {
        public IntObject(object value) : base() {
            initialize(convert<System.Int64>(value));
        }
    }

    class FloatObject : Object {
        public FloatObject(object value) : base() {
            initialize(convert<System.Double>(value));
        }
    }

    class BoolObject : Object {
        public BoolObject(object value) : base() {
            initialize(convert<System.Boolean>(value));
        }
    }

    class StringObject : Object {
        public StringObject(object value) : base() {
            initialize(convert<System.String>(value));
        }
        public override string Repr()
        {
            return $"'{ToString()}'";
        }
    }

    class ArrayObject : Object {
        public ArrayObject(object value) : base() {
            initialize(convert<List<object>>(value));
            this.properties = new Dictionary<object, object>{
                {"append", "append"}
            };
        }

        public override string ToString()
        {
            List<string> reprs = new List<string>{};
            foreach (Object element in value){
                reprs.Add(Interpreter.__interpreter__.visit(element).Repr());
            }
            return string.Join(", ", reprs);
            //return "[{', '.join([repr(__interpreter__.visit(i)) for i in this.value])}]";
        }

        public void append(object _object){
            this.value.Add(_object);
        }
    }

    class Record : Object {
        public Var token;
        public List<DeclaredParam> parameters;
        public Record(Var token){
            this.token = token;
            this.parameters = new List<DeclaredParam>{};
        }
        public override string ToString()
        {
            return $"<record definition {token.value}>";
        }
    }

    class RecordObject : Object {
        public Record baseRecord;
        public RecordObject(Record baseRecord){
            this.baseRecord = baseRecord;
            this.properties = new Dictionary<object, object>{};
        }
        public override string ToString()
        {
            return $"<record object {baseRecord.token.value}>";
        }
    }

    class ClassDefinition : Object {
        public static List<string> special_subroutines = new List<string>{
            "STR", "REPR", "INIT"
        };
        public Var token;
        public List<Assign> static_values;
        public List<Subroutine> subroutines;

        public ClassDefinition(Var token, List<Assign> static_values, List<Subroutine> subroutines){
            this.token = token;
            this.static_values = static_values;
            this.subroutines = subroutines;
        }

        public override string ToString()
        {
            if (properties.Keys.Contains("STR")){
                return Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["STR"], new List<Param>{})).ToString();
            }
            return $"<class definition {token.value}>";
        }

        public override string Repr()
        {
            if (properties.Keys.Contains("REPR")){
                return Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["REPR"], new List<Param>{})).ToString();
            }
            return ToString();
        }
    }

    class ClassInstance : Object {
        public ClassDefinition baseClass;
        public ClassInstance(ClassDefinition baseClass){
            this.baseClass = baseClass;
            this.properties = new Dictionary<object, object>(baseClass.properties);
        }

        public override string ToString()
        {
            if (properties.Keys.Contains("STR")){
                return Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["STR"], new List<Param>{})).ToString();
            }
            return $"<class instance {baseClass.token.value}>";
        }

        public override string Repr()
        {
            if (properties.Keys.Contains("REPR")){
                return Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["REPR"], new List<Param>{})).ToString();
            }
            return ToString();
        }
    }

    class BuiltinModule : Object {
        
    }

    class _math : BuiltinModule {
        public _math(){
            this.properties = new Dictionary<object, object>{
                {"sqrt", "sqrt"}
            };
        }
        public Object sqrt(Object v){
            return Object.create(Math.Sqrt(v.value));
        }
    }

    [System.Serializable]
    public class ParseError : System.Exception
    {
        public string message, lineText = "";
        public int lineno, column;
        public ParseError() { }
        public ParseError(string message) : base(message) { }
        public ParseError(string message, System.Exception inner) : base(message, inner) { }

        public ParseError(string message, int lineno, int column){
            this.message = message;
            this.lineno = lineno;
            this.column = column;
        }

        public ParseError(string message, int lineno, int column, string lineText){
            this.message = message;
            this.lineno = lineno;
            this.column = column;
            this.lineText = lineText;
        }

        protected ParseError(
            System.Runtime.Serialization.SerializationInfo info,
            System.Runtime.Serialization.StreamingContext context) : base(info, context) { }

        public override string Message {
            get {
                string ret = $"\n  Line {lineno}:\n";
                if (lineText != "") ret += $"  {lineText}\n  {new String(' ', column-1)}^\n";
                return ret + $"{message}";
            }
        }
    }

    class IfStatement : AST {
        public AST condition;
        public Compound consequence;
        public List<AST> alternatives;
        public IfStatement(AST condition){
            this.condition = condition;
            this.alternatives = new List<AST>{};
        }
    }
        

    class WhileStatement : AST {
        public AST condition;
        public Compound consequence;
        public WhileStatement(AST condition){
            this.condition = condition;
        }
    }

    class ForLoop : AST {
        public Var variable;
        public AST _iterator, start, end, step;
        public bool to_step;
        public Compound loop;
        public ForLoop(Var variable, AST iterator=null){
            this.variable = variable;
            this._iterator = iterator;
            this.to_step = false;
        }
    }

    class RepeatUntilStatement : WhileStatement {
        public RepeatUntilStatement(AST condition) : base(condition) {
            this.condition = condition;
        }
    }

    class TryCatch : AST {
        public Compound try_compound, catch_compound;
        public TryCatch(Compound try_compound, Compound catch_compound){
            this.try_compound = try_compound;
            this.catch_compound = catch_compound;
        }
    }

    class Parser {
        public Lexer lexer;
        public int token_num;
        public Parser(Lexer lexer){
            this.lexer = lexer;
            this.token_num = 0;
        }

        public Token EOF(){
            return new Token("", TokenType.EOF, lexer.lines.Count-1, lexer.lines[lexer.lines.Count-3].Length+1);
        }

        public Token _get_next_token(){
            token_num += 1;
            if (token_num >= lexer.tokens.Count) return EOF();
            return lexer.tokens[token_num];
        }

        public void eat(TokenType token_type){
            if (current_token.type == token_type) _get_next_token();
            else {
                throw new ParseError(
                    $"Expected {token_type} but found {current_token.error_format()}",
                    current_token.column, current_token.column,
                    lexer.lines[current_token.lineno-1]
                );
            }
        }

        public void eat_gap(){
            while (current_token.type == TokenType.NEWLINE){
                eat(current_token.type);
            }
        }

        public Token current_token { 
            get {
                if (token_num >= lexer.tokens.Count) return EOF();
                return lexer.tokens[token_num];
            }
        }

        public Token next_token { 
            get {
                if (token_num + 1 >= lexer.tokens.Count) return EOF();
                return lexer.tokens[token_num + 1];
            }
        }

        public void error(){
            throw new ParseError(
                $"Unexpected token {current_token.error_format()}", 
                current_token.column, current_token.column,
                lexer.lines[current_token.lineno-1]
            );
        }

        public Compound program(){
            return compound();
        }

        public Compound compound(){
            List<AST> nodes = statement_list();
            Compound node = new Compound();
            node.children = nodes;
            return node;
        }

        public List<AST> statement_list(){
            List<AST> results = new List<AST>{};
            eat_gap();
            if (current_token.type != TokenType.NEWLINE){
                AST node = statement();
                if (node != null) results.Add(node);
            }


            while (current_token.type == TokenType.NEWLINE){
                eat_gap();
                AST node = statement();
                if (node != null) results.Add(node);
            }

            if (current_token.type == TokenType.ID) error();

            return results;
        }

        public AST statement(){
            AST node;
            switch (current_token.type){
                case TokenType.ID:
                case TokenType.CONSTANT:
                    Var v = variable();
                    if (current_token.type == TokenType.LPAREN) node = subroutine_call(v);
                    else node = assignment_statement(v);
                    break;
            
                case TokenType.MAGIC:
                    node = magic_function();
                    break;
                case TokenType.IF:
                    node = if_statement();
                    eat(TokenType.KEYWORD);
                    break;
                case TokenType.WHILE:
                    node = while_statement();
                    eat(TokenType.KEYWORD);
                    break;
                case TokenType.REPEAT:
                    node = repeat_until_statement();
                    break;
                case TokenType.FOR:
                    node = for_loop();
                    break;
                case TokenType.RECORD:
                    return record_definition();
                case TokenType.TRY:
                    return try_catch();
                case TokenType.SUBROUTINE:
                    return subroutine();
                case TokenType.CLASS:
                    return class_definition();
                default:
                    //node = empty()
                    return null;

            }
            return node;
        }

        public Assign assignment_statement(Var var){
            Var left = var;
            Token token = current_token;
            if (current_token.type == TokenType.COLON){
                eat(TokenType.COLON);
                eat(TokenType.ID); // TYPE
            }
            eat(TokenType.ASSIGN);
            AST right = expr();
            Assign node = new Assign(left, token, right);
            return node;
        }

        public Var variable(){
            if (current_token.type == TokenType.CONSTANT) eat(TokenType.CONSTANT);
            Var node = new Var(current_token);
            eat(TokenType.ID);
            while (current_token.type == TokenType.LS_PAREN || current_token.type == TokenType.DOT){
                if (current_token.type == TokenType.LS_PAREN){
                    eat(TokenType.LS_PAREN);
                    node.array_indexes.Add(expr());
                    eat(TokenType.RS_PAREN);
                }
                else if (current_token.type == TokenType.DOT){
                    eat(TokenType.DOT);
                    node.array_indexes.Add(id());
                }
            }
            return node;
        }

        public StringObject id(){
            Token token = current_token;
            eat(TokenType.ID);
            return new StringObject(token.value);
        }

        public NoOp empty(){
            return new NoOp();
        }

        public AST factor(){
            Token token = current_token;
            AST node;
            switch (token.type){
                case TokenType.ADD:
                    eat(TokenType.ADD);
                    node = new UnaryOp(token, factor());
                    return node;
                case TokenType.SUB:
                    eat(TokenType.SUB);
                    node = new UnaryOp(token, factor());
                    return node;
                case TokenType.NOT:
                    eat(TokenType.NOT);
                    node = new UnaryOp(token, factor());
                    return node;
                case TokenType.INT:
                case TokenType.FLOAT:
                case TokenType.BOOLEAN:
                case TokenType.STRING:
                    eat(token.type);
                    return Object.create(token.value, token.type);
                
                case TokenType.LPAREN:
                    eat(TokenType.LPAREN);
                    node = expr();
                    eat(TokenType.RPAREN);
                    return node;
                case TokenType.LS_PAREN:
                    eat(TokenType.LS_PAREN);
                    node = array();
                    eat(TokenType.RS_PAREN);
                    return node;
                
                case TokenType.MAGIC:
                    return magic_function();
                default:
                    node = variable();
                    if (current_token.type == TokenType.LPAREN) node = subroutine_call((Var)node);
                    return node;
            }
        }

        public AST term(){ // POW is right associative, which is unique
            AST node = factor();

            if (current_token.type == TokenType.POW){
                Token token = current_token;
                eat(token.type);
        
                node = new BinOp(node, token, term());
            }
        
            return node;
        }

        public AST term2(){        
            AST node = term();
            List<TokenType> targets = new List<TokenType>{TokenType.MUL, TokenType.DIV, TokenType.INT_DIV, TokenType.MOD};
            while (targets.Contains(current_token.type)){
                Token token = current_token;
                eat(token.type);
            
                node = new BinOp(node, token, term());
            }
            return node;
        }

        public AST term3(){        
            AST node = term2();
            List<TokenType> targets = new List<TokenType>{TokenType.ADD, TokenType.SUB};
            while (targets.Contains(current_token.type)){
                Token token = current_token;
                eat(token.type);
            
                node = new BinOp(node, token, term2());
            }
            return node;
        }

        public AST term4(){        
            AST node = term3();
            List<TokenType> targets = new List<TokenType>{
                TokenType.LT,
                TokenType.GT,
                TokenType.LE,
                TokenType.GE,
                TokenType.EQ,
                TokenType.NE
            };
            while (targets.Contains(current_token.type)){
                Token token = current_token;
                eat(token.type);
            
                node = new BinOp(node, token, term3());
            }
            return node;
        }

        public AST term5(){        
            AST node = term4();
            List<TokenType> targets = new List<TokenType>{TokenType.AND, TokenType.OR};
            while (targets.Contains(current_token.type)){
                Token token = current_token;
                eat(token.type);
            
                node = new BinOp(node, token, term4());
            }
            return node;
        }

        public AST expr(){
            return term5();
        }

        public Magic magic_function(){
            Token token = current_token;
            List<TokenType> targets = new List<TokenType>{TokenType.EOF, TokenType.NEWLINE, TokenType.RPAREN};
            eat(TokenType.MAGIC);
            List<AST> parameters = new List<AST>{};
            if (!targets.Contains(current_token.type)){
                parameters.Add(expr());
                while (current_token.type == TokenType.COMMA){
                    eat(TokenType.COMMA);
                    parameters.Add(expr());
                }
            }
            Magic node = new Magic(token, parameters);

            return node;
        }

        public DeclaredParam declare_param(){
            Var v = variable();
            DeclaredParam node = new DeclaredParam(v, null);
            Token token = current_token;
            if (current_token.type == TokenType.COLON){
                eat(TokenType.COLON);
                eat(TokenType.ID); // TYPE
            }

            return node;
        }

        public Param param(){
            Param node = new Param(expr(), null);
            return node;
        }

        public Subroutine subroutine(){
            eat(TokenType.SUBROUTINE);
            Token token = current_token;
            eat(TokenType.ID);
            eat(TokenType.LPAREN);
            List<DeclaredParam> parameters = new List<DeclaredParam>{};
            if (current_token.type != TokenType.RPAREN){
                parameters.Add(declare_param());
                while (current_token.type == TokenType.COMMA){
                    eat(TokenType.COMMA);
                    parameters.Add(declare_param());
                }
            }
            eat(TokenType.RPAREN);
            Compound _compound = compound();
            eat(TokenType.KEYWORD);
            return new Subroutine(token, parameters, _compound);
        }

        public SubroutineCall subroutine_call(Var v){
            eat(TokenType.LPAREN);

            List<Param> parameters = new List<Param>{};
            if (current_token.type != TokenType.RPAREN){
                parameters.Add(param());
                while (current_token.type == TokenType.COMMA){
                    eat(TokenType.COMMA);
                    parameters.Add(param());
                }
            }
            eat(TokenType.RPAREN);
            return new SubroutineCall(v, parameters);
        }

        public IfStatement if_statement(){
            Token token = current_token;
            eat(TokenType.IF);

            AST condition = expr();
            eat_gap();
            eat(TokenType.THEN);

            Compound consequence = compound();

            List<AST> alternatives = new List<AST>{};
            if (current_token.type == TokenType.ELSE && next_token.type == TokenType.IF){
                alternatives.Add(elseif_statement());
            }
            else if (current_token.type == TokenType.ELSE){
                alternatives.Add(else_statement());
            }
            
            IfStatement node = new IfStatement(condition);
            node.consequence = consequence;
            node.alternatives = alternatives;
            return node;
        }

        public IfStatement elseif_statement(){
            eat(TokenType.ELSE);
            return if_statement();
        }
        
        public Compound else_statement(){
            eat(TokenType.ELSE);
            return compound();
        }

        public WhileStatement while_statement(){
            Token token = current_token;
            eat(TokenType.WHILE);
            AST condition = expr();
            Compound consequence = compound();

            WhileStatement node = new WhileStatement(condition);
            node.consequence = consequence;

            return node;
        }

        public RepeatUntilStatement repeat_until_statement(){
            Token token = current_token;
            eat(TokenType.REPEAT);
            
            Compound consequence = compound();
            eat_gap();
            eat(TokenType.UNTIL);
            AST condition = expr();

            RepeatUntilStatement node = new RepeatUntilStatement(condition);
            node.consequence = consequence;

            return node;
        }

        public ArrayObject array(){
            List<AST> values = new List<AST>{};
            if (current_token.type != TokenType.RS_PAREN){
                eat_gap();
                values.Add(expr());
                eat_gap();
                while (current_token.type == TokenType.COMMA){
                    eat_gap();
                    eat(TokenType.COMMA);
                    eat_gap();
                    values.Add(expr());
                    eat_gap();
                }
            }
            eat_gap();
            //print(values)
            return new ArrayObject(values);
        }

        public ForLoop for_loop(){
            eat(TokenType.FOR);
            Var variable = this.variable();
            ForLoop f = new ForLoop(variable, null);
            if (current_token.type == TokenType.ASSIGN){
                f.to_step = true;
                // FOR ID ASSIGN expr TO expr (STEP expr)? statement_list ENDFOR
                eat(TokenType.ASSIGN);
                f.start = expr();
                eat(TokenType.TO);
                f.end = expr();
                if (current_token.type == TokenType.STEP){
                    eat(TokenType.STEP);
                    f.step = expr();
                }
                eat_gap();
                f.loop = compound();
            }
            else if (current_token.type == TokenType.IN){
                // FOR variable IN expr statement_list ENDFOR
                eat(TokenType.IN);
                f._iterator = expr();
                eat_gap();
                f.loop = compound();
            }
            eat(TokenType.KEYWORD);
            return f;
        }

        public Record record_definition(){
            eat(TokenType.RECORD);
            Var v = variable();
            Record node = new Record(v);
            eat_gap();
            while (current_token.type != TokenType.KEYWORD){
                eat_gap();
                node.parameters.Add(declare_param());
                eat_gap();
            }
            
            eat_gap();
            eat(TokenType.KEYWORD);
            return node;
        }

        public TryCatch try_catch(){
            eat(TokenType.TRY);
            Compound try_compound = compound();
            eat(TokenType.CATCH);
            Compound catch_compound = compound();
            eat(TokenType.KEYWORD);

            return new TryCatch(try_compound, catch_compound);
        }

        public ClassDefinition class_definition(){
            eat(TokenType.CLASS);
            Var variable = this.variable();
            List<Assign> static_values = new List<Assign>{};
            List<Subroutine> subroutines = new List<Subroutine>{};
            eat_gap();
            while (current_token.type == TokenType.SUBROUTINE || current_token.type == TokenType.ID){
                eat_gap();
                if (current_token.type == TokenType.SUBROUTINE){
                    subroutines.Add(subroutine());
                }
                else if (current_token.type == TokenType.ID){
                    Var v = this.variable();
                    static_values.Add(assignment_statement(v));
                }
                eat_gap();
            }
            eat_gap();
            eat(TokenType.KEYWORD);

            return new ClassDefinition(variable, static_values, subroutines);
        }

        public Compound parse(){
            Compound node = program();
            if (current_token.type != TokenType.EOF){
                error();
            }

            return node;
        }


    }

    class Interpreter {
        public static Interpreter __interpreter__;

        public Interpreter(){
            __interpreter__ = this;
        }

        public Object visit(object node){
            return Object.create(""); // TEMP FUNCTION
        }
    }
}