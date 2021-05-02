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
        public AST ShallowCopy()
        {
           return (AST) this.MemberwiseClone();
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
        public Var left;
        public AST right;
        public Token op, token;
        public Assign(Var left, Token op, AST right){
            this.left = left;
            this.token = this.op = op;
            this.right = right;
        }
    }
    class Var : AST {
        public Token token;
        public string name;
        public List<AST> array_indexes;
        public Var(Token token){
            this.token = token;
            this.name = token.value;
            array_indexes = new List<AST>{};
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

    class Subroutine : Object {
        public Var token;
        public List<DeclaredParam> parameters;
        public Compound compound;
        public bool builtin;
        public AST classBase; // NOTE: ClassObject not done yet!
        public Subroutine(Var token, List<DeclaredParam> parameters, Compound compound){
            this.token = token;
            this.parameters = parameters;
            this.compound = compound;
            this.builtin = false;
            this.classBase = null;
        }
        
        public override string ToString()
        {
            return $"<subroutine {token.name}>";
        }

        public override string Repr()
        {
            return ToString();
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

    class BuiltinSubroutine : Object {
        public MethodInfo methodInfo;
        public BuiltinSubroutine(MethodInfo methodInfo){
            this.methodInfo = methodInfo;
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
                case "System.Boolean":
                    return new BoolObject(value);
                case "System.String":
                case "System.Char":
                    return new StringObject(value);
                case "System.Collections.Generic.List`1[System.Object]":
                    var arr = new ArrayObject(new List<object>{});
                    arr.value = value;
                    return arr;
            }
            Console.WriteLine($"Failed; {value.GetType()}");
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
                object ret;
                if (index is Object) index = ((Object)index).value;
                if (index is int || index is long) ret = this.value[Convert.ToInt32(index)];
                else ret =  this.properties[Convert.ToString(index)];

                return ret;
            }
            set {
                //Console.WriteLine($"set {index} {index.GetType()} {this} {this.value.GetType()}");
                if (index is Object) index = ((Object)index).value;
                if (index is int || index is long){ this.value[Convert.ToInt32(index)] = (AST)value; }
                if (index is string){ this.properties[Convert.ToString(index)] = (AST)value; }
            }
        }

        public override string ToString()
        {
            return Convert.ToString(this.value);
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
        public ArrayObject(List<object> value) : base() {
            initialize(value);
            this.properties = new Dictionary<object, object>{
                {"append", new BuiltinSubroutine(this.GetType().GetMethod("append"))}
            };
        }

        public override string ToString()
        {
            List<string> reprs = new List<string>{};
            foreach (AST element in value){
                reprs.Add(Interpreter.__interpreter__.visit(element).Repr());
            }
            return $"[{string.Join(", ", reprs)}]";
            //return "[{', '.join([repr(__interpreter__.visit(i)) for i in this.value])}]";
        }

        public void append(AST _object){
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
            return $"<record definition {token.name}>";
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
            return $"<record object {baseRecord.token.name}>";
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
                return Convert.ToString(Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["STR"], new List<Param>{})));
            }
            return $"<class definition {token.name}>";
        }

        public override string Repr()
        {
            if (properties.Keys.Contains("REPR")){
                return Convert.ToString(Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["REPR"], new List<Param>{})));
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
                return Convert.ToString(Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["STR"], new List<Param>{})));
            }
            return $"<class instance {baseClass.token.name}>";
        }

        public override string Repr()
        {
            if (properties.Keys.Contains("REPR")){
                return Convert.ToString(Interpreter.__interpreter__.visit(new SubroutineCall((Var)properties["REPR"], new List<Param>{})));
            }
            return ToString();
        }
    }

    class BuiltinModule : Object {
        public void registerFunctions(Type T, List<string> functions){
            foreach (string f in functions){
                this.properties[f] = new BuiltinSubroutine(T.GetMethod(f));
            }
        }
    }

    class _math : BuiltinModule {
        public _math(){
            this.properties = new Dictionary<object, object>{
                {"sqrt", new BuiltinSubroutine(this.GetType().GetMethod("sqrt"))}
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
            Var v = variable();
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
            return new Subroutine(v, parameters, _compound);
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
            var obj = new ArrayObject(new List<object>{});
            obj.value = values;
            return obj;
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

    class VariableScope {
        public string name;
        public VariableScope enclosing_scope;
        public Dictionary<string, AST> _variables;
        public VariableScope(string name, VariableScope enclosing_scope){
            this.name = name;
            this.enclosing_scope = enclosing_scope;
            _variables = new Dictionary<string, AST>{};
        }
        
        public void insert(Var v, AST value){
            if (Interpreter.__interpreter__.tracer != null) Interpreter.__interpreter__.tracer.onchange(v.name, value);
            _variables[v.name] = value;
        }
        
        public AST get(Var v){
            if (_variables.TryGetValue(v.name, out AST value)) return value;
            while (enclosing_scope != null){
                return enclosing_scope.get(v);
            }
            
            throw new Exception($"variable '{v.name}' does not exist");
        }
    }

    class NodeVisitor {
        public Object visit(AST node){
            string method_name = "visit_" + node.GetType().Name;
            var func = this.GetType().GetMethod(
                method_name, 
                0,
                new Type[]{ typeof(AST) }
            );
            if (func == null){
                generic_visit(node);
            }
            return (Object)func.Invoke(this, new object[]{ node });
        }

        public void generic_visit(AST node){
            throw new Exception($"No visit_{node.GetType().Name} method");
        }
    }

    class _BUILTINS : BuiltinModule {
        public static _BUILTINS instance;
        public _BUILTINS(){
            instance = this;
            this.properties = new Dictionary<object, object>{
                {"SQRT", new BuiltinSubroutine(this.GetType().GetMethod("SQRT"))},
                {"Int", new BuiltinSubroutine(this.GetType().GetMethod("Int"))}

            };
            /*registerFunctions(
                this.GetType(),
                new List<string>{
                    //"INPUT",
                    //"LEN",
                    //"POSITION",
                    //"SUBSTRING",
                    //"STRING_TO_INT",
                    //"STRING_TO_REAL",
                    //"INT_TO_STRING",
                    //"REAL_TO_STRING",
                    //"CHAR_TO_CODE",
                    //"CODE_TO_CHAR",
                    //"RANDOM_INT",
                    //"SQRT",
                    "Int"//,
                    //"String"
                }
            );*/
        }
        public Object SQRT(Object v){
            return Object.create(Math.Sqrt(v.value));
        }

        public Object Int(Object value){
            return new IntObject(value.value);
        }
    }

    class Interpreter : NodeVisitor {
        public static Interpreter __interpreter__;
        public Parser parser;
        public VariableScope current_scope;
        public bool RETURN, CONTINUE, BREAK;
        public Object RETURN_VALUE;
        public Utilities.Tracker tracer;

        public Interpreter(Parser parser, Utilities.Tracker tracer){
            
            __interpreter__ = this;
            this.parser = parser;
            this.current_scope = null;
            this.RETURN = false;
            this.CONTINUE = false;
            this.BREAK = false;
            this.tracer = tracer;
        }

        public Object visit_BinOp(AST _node){
            BinOp node = (BinOp)_node;
            object result;

            switch (node.op.type){
                case TokenType.ADD:
                    result = visit(node.left).value + visit(node.right).value;
                    break;
                case TokenType.SUB:
                    result = visit(node.left).value - visit(node.right).value;
                    break;
                case TokenType.MUL:
                    result = visit(node.left).value * visit(node.right).value;
                    break;
                case TokenType.DIV:
                    result = (double)visit(node.left).value / visit(node.right).value;
                    break;
                case TokenType.INT_DIV:
                    result = (long)visit(node.left).value / (long)visit(node.right).value;
                    break;
                case TokenType.MOD:
                    result = visit(node.left).value % visit(node.right).value;
                    break;
                case TokenType.POW:
                    result = Math.Pow(visit(node.left).value, visit(node.right).value);
                    break;
                
                case TokenType.GT:
                    result = visit(node.left).value > visit(node.right).value;
                    break;
                case TokenType.GE:
                    result = visit(node.left).value >= visit(node.right).value;
                    break;
                case TokenType.EQ:
                    result = visit(node.left).value == visit(node.right).value;
                    break;
                case TokenType.NE:
                    result = visit(node.left).value != visit(node.right).value;
                    break;
                case TokenType.LT:
                    result = visit(node.left).value < visit(node.right).value;
                    break;
                case TokenType.LE:
                    result = visit(node.left).value <= visit(node.right).value;
                    break;
                case TokenType.AND:
                    result = visit(node.left).value && visit(node.right).value;
                    break;
                case TokenType.OR:
                    result = visit(node.left).value || visit(node.right).value;
                    break;
                default:
                    throw new Exception($"Unsupported BinOp {node.op.type}");
            }

            return Object.create(result);
        }

        public Object visit_UnaryOp(AST _node){
            UnaryOp node = (UnaryOp)_node;
            object result;
            switch (node.op.type){
                case TokenType.ADD:
                    result = +visit(node.expr).value;
                    break;
                case TokenType.SUB:
                    result = -visit(node.expr).value;
                    break;
                case TokenType.NOT:
                    result = !visit(node.expr).value;
                    break;
                default:
                    throw new Exception($"Unsupported UnaryOp {node.op.type}");
            }
            return Object.create(result);
        }

        public Object visit_IntObject(AST node){ return (IntObject)node; }
        public Object visit_FloatObject(AST node){ return (FloatObject)node; }
        public Object visit_BoolObject(AST node){ return (BoolObject)node; }
        public Object visit_StringObject(AST node){ return(StringObject) node; }
        public Object visit_ArrayObject(AST node){ return (ArrayObject)node; }
        public Object visit_RecordObject(AST node){ return (RecordObject)node; }

        public void visit_Compound(AST _node){
            Compound node = (Compound)_node;
            foreach (var child in node.children){
                if (RETURN || BREAK || CONTINUE) break;
                visit(child);
            }
        }

        public void visit_NoOp(AST node){}

        public Object set_element(Object L, List<AST> indexes, AST value){
            AST target = visit(indexes[0]);
            if (indexes.Count < 2){
                L[target] = value;
            }
            else {
                L[target] = set_element((Object)L[target], indexes.Skip(1).ToList(), value);
            }
            return L;
        }

        public void visit_Assign(AST _node){
            Assign node = (Assign)_node;
            var var_name = node.left.name;
            if (current_scope._variables.ContainsKey(var_name)){
                var val = visit_Var(node.left, false);
                
                if (node.left.array_indexes.Count > 0){
                    val = set_element(
                        val, 
                        node.left.array_indexes, 
                        visit(node.right)
                    );
                    return;
                }
            }
            current_scope.insert(node.left, visit(node.right));
        }

        public Object visit_Var(AST _node){
            Var node = (Var)_node;
            return visit_Var(node, true);
        }

        public Object visit_Var(Var node, bool traverse_lists){
            string var_name = node.name;
            Object val = (Object)current_scope.get(node);
            if (traverse_lists){
                foreach (var i in node.array_indexes){
                    Object target = (Object)visit(i);
                    
                    var temp = val[target];
                    // when a StringObject is sliced a char is returned but we want a StringObject
                    //print(type(val))
                    if (!(temp is Object)) val = Object.create(temp);
                    else { val = (Object)temp; }
                    val = (Object)visit(val);
                    //print(f"val type: {type(val)}")
                }
            }
            return val;
        }

        public Object visit_Magic(AST _node){
            Magic node = (Magic)_node;
            switch (node.token.value){
                case "OUTPUT":
                    List<string> values = new List<string>{};
                    for (int i = 0; i < node.parameters.Count; i++){
                        AST n = node.parameters[i];
                        Console.Write(Convert.ToString(visit(n)));
                        if (i < node.parameters.Count - 1) Console.Write(" ");
                    }
                    Console.Write("\n");
                    break;
                case "USERINPUT":
                    return Object.create(Console.ReadLine());
                case "RETURN":
                    RETURN_VALUE = node.parameters.Count > 0 ? visit(node.parameters[0]) : null;
                    RETURN = true;
                    break;
                case "CONTINUE":
                    CONTINUE = true;
                    break;
                case "BREAK":
                    BREAK = true;
                    break;
            }
            return null;
        }

        public void visit_Subroutine(AST _node){
            Subroutine node = (Subroutine)_node;
            current_scope.insert(node.token, node);
        }

        public void visit_Record(AST _node){
            Record node = (Record)_node;
            current_scope.insert(node.token, node);
        }

        public RecordObject create_RecordObject(SubroutineCall node, Record baseRecord){
            RecordObject record_object = new RecordObject(baseRecord);
            for (int i = 0; i < baseRecord.parameters.Count; i++){
                string name = baseRecord.parameters[i].variable.name;
                Param param = node.parameters[i];
                record_object.properties[name] = visit(param.value);
            }
            return record_object;
        }

        public Object visit_SubroutineCall(AST _node){
            SubroutineCall node = (SubroutineCall)_node;

            Object function = visit(node.subroutine_token);

            if (function is Record){
                return create_RecordObject(node, (Record)function);
            }
            else if (function is Subroutine){
                Subroutine subroutine = (Subroutine)function;
                VariableScope function_scope = new VariableScope("function_scope", current_scope);
            
                if (subroutine.classBase != null){
                    function_scope.insert(new Var(new Token("this", TokenType.ID)), subroutine.classBase);
                }
                
                
                if (subroutine.parameters.Count != node.parameters.Count){
                    throw new Exception("mismatched function parameters");
                }
                for (int i = 0; i < subroutine.parameters.Count; i++){
                    DeclaredParam param_definition = subroutine.parameters[i];
                    Param parameter = node.parameters[i];
                    function_scope.insert(param_definition.variable, visit(parameter.value));
                }
                current_scope = function_scope;
                // execute function
                RETURN_VALUE = null;
                RETURN = false;
                visit(subroutine.compound);
                RETURN = false;
                Object result = RETURN_VALUE;
                RETURN_VALUE = null;
                current_scope = current_scope.enclosing_scope;

                //Console.WriteLine(function_scope._variables)
                return result;
            }
            else if (function is ClassDefinition){
                ClassDefinition cls = (ClassDefinition)function;
                Var tok = (Var)node.subroutine_token.ShallowCopy();
                tok.array_indexes.Add(Object.create("INIT"));
                SubroutineCall temp = new SubroutineCall(tok, node.parameters);
                //Console.WriteLine("creating class instance...")
                return create_ClassInstance(temp, cls);
            }
            else if (function is BuiltinSubroutine){
                return prcoess_BuiltinSubroutineCall((BuiltinSubroutine)function, node);
            }

            return null;
        }

        public void visit_IfStatement(AST _node){
            IfStatement node = (IfStatement)_node;
            if (Convert.ToBoolean(visit(node.condition).value)){
                visit(node.consequence);
            }
            else {
                foreach (var statement in node.alternatives){
                    visit(statement);
                }
            }
        }

        public void visit_WhileStatement(AST _node){
            WhileStatement node = (WhileStatement)_node;
            while (Convert.ToBoolean(visit(node.condition).value)){
                visit(node.consequence);
                if (CONTINUE){
                    CONTINUE = false;
                    continue;
                }
                if (BREAK){
                    BREAK = false;
                    break;
                }
            }
        }

        public void visit_RepeatUntilStatement(AST _node){
            RepeatUntilStatement node = (RepeatUntilStatement)_node;

            while (true){
                visit(node.consequence);
                if (CONTINUE){
                    CONTINUE = false;
                    continue;
                }
                if (BREAK){
                    BREAK = false;
                    break;
                }

                if (Convert.ToBoolean(visit(node.condition).value)) break;
            }
        }

        public void visit_ForLoop(AST _node){
            ForLoop node = (ForLoop)_node;

            if (node.to_step){
                long step = node.step != null ? (long)visit(node.step).value : 1L;
                for (long i = (long)visit(node.start).value; i < visit(node.end).value+1; i += step){
                    current_scope.insert(node.variable, Object.create(i));
                    visit(node.loop);
                    if (CONTINUE){
                        CONTINUE = false;
                        continue;
                    }
                    if (BREAK){
                        BREAK = false;
                        break;
                    }
                }
            }
            else {
                var iterator = visit(node._iterator).value;
                foreach (var i in iterator){
                    var current = i;
                    // strings :
                    if (i is Object) current = visit(i).value;
                    current_scope.insert(node.variable, Object.create(current));
                    visit(node.loop);
                    if (CONTINUE){
                        CONTINUE = false;
                        continue;
                    }
                    if (BREAK){
                        BREAK = false;
                        break;
                    }
                }
            }
        }

        public void visit_TryCatch(AST _node){
            TryCatch node = (TryCatch)_node;
            try {
                visit(node.try_compound);
            }
            catch {
                visit(node.catch_compound);
            }
        }

        public ClassDefinition visit_ClassDefinition(AST _node){
            ClassDefinition node = (ClassDefinition)_node;
            current_scope.insert(node.token, node);
            foreach (var v in node.static_values){
                node.properties[v.left.name] = visit(v.right);
            }
            foreach (var f in node.subroutines){
                f.classBase = node;
                node.properties[f.token.name] = f;
            }
            //Console.WriteLine(node.properties)
            return node;
        }

        public ClassInstance create_ClassInstance(SubroutineCall node, ClassDefinition baseClass){
            ClassInstance class_instance = new ClassInstance(baseClass);
            foreach (var name in class_instance.properties.Keys){
                var func = class_instance.properties[name];
                if (func is Subroutine){
                    ((Subroutine)func).classBase = class_instance;
                }
            }

            if (class_instance.properties.TryGetValue("INIT", out var initialise_function)){
                node.subroutine_token = (Var)initialise_function;
                visit(node);
            }

            return class_instance;
        }

        public BuiltinSubroutine visit_BuiltinSubroutine(AST _node){ return (BuiltinSubroutine)_node; }

        public Object prcoess_BuiltinSubroutineCall(BuiltinSubroutine node, SubroutineCall call){
            object obj;
            List<AST> old_indexes = call.subroutine_token.array_indexes;
            if (call.subroutine_token.array_indexes.Count > 0){
                List<AST> new_indexes = new List<AST>(call.subroutine_token.array_indexes);
                new_indexes.RemoveAt(call.subroutine_token.array_indexes.Count-1);
                call.subroutine_token.array_indexes = new_indexes;
                obj = visit_Var(call.subroutine_token);
                call.subroutine_token.array_indexes = old_indexes;
            }
            else obj = _BUILTINS.instance;



            List<AST> visited_params = new List<AST>{};
            foreach (var p in call.parameters){
                visited_params.Add(visit(p.value));
            }
            var result = node.methodInfo.Invoke(
                obj,
                visited_params.ToArray()
            );
            if (result == null) return null;
            return (Object)result;
        }

        public void interpret(){
            var tree = parser.parse();
            var global_scope = new VariableScope("global", null);
            current_scope = global_scope;

            // add _BUILTINS and all BuiltinModules
            
            foreach (Type t in Utilities.Utilities.GetInheritedClasses(typeof(BuiltinModule))){
                BuiltinModule instance = (BuiltinModule)Activator.CreateInstance(t);
                Var v = new Var(new Token(t.Name.Skip(1).ToString(), TokenType.ID));
                current_scope.insert(v, instance);

                if (t.Name == "_BUILTINS"){
                    foreach (string name in instance.properties.Keys){
                        BuiltinSubroutine s = (BuiltinSubroutine)instance.properties[name];
                        Var _v = new Var(new Token(name, TokenType.ID));
                        current_scope.insert(_v, s);
                    }
                }
            }

            visit(tree);
        }

    }
}