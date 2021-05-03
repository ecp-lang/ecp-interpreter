using System;
using System.Collections.Generic;
using System.IO;

namespace Ecp
{
    class Program
    {
        static void Main(string[] args)
        {
            List<string> _args = new List<string>(args);
            string filePath = args[0];
            string text = "";
            try {
                text = File.ReadAllText(filePath);
            }
            catch (Exception ex){
                Console.WriteLine($"an Exception occured when trying to open the file: {ex.Message}");
                return;
            }
            //string file = args[]
            //Console.WriteLine("C# Lexer test");
            Lexer lexer = new Lexer();
            List<Token> tokens = lexer.lexString(text);
            //Utilities.TablePrinter table = new Utilities.TablePrinter("Token Value", "Token Type");
            //foreach (Token token in tokens){
            //    string v = token.value.ToString().Replace("\n", "\\n");
            //    table.AddRow(v, token.type.ToString());
            //}
            //table.Print();

            Parser parser = new Parser(lexer);
            Utilities.Tracker tracer = null;
            if (_args.Contains("--debug")){
                tracer = new Utilities.Tracker(new List<string>{"a"}, true);
            }
            Interpreter interpreter = new Interpreter(parser, tracer);
            interpreter.interpret();
            //interpreter.tracer.displayTraceTable(new List<string>{"a"});

            //var t1 = Object.create(12L);
            //var t2 = Object.create(13L);
            //Console.WriteLine((t1 + t2).value);
            //var l1 = Object.create(new List<object>{Object.create("1st element")});
            //Console.WriteLine(l1[0]);
        }
    }
}
