using System;
using System.Collections.Generic;
using System.IO;

namespace Ecp
{
    class Program
    {
        static void Main(string[] args)
        {
            string filePath = args[0];
            string text = "";
            if (File.Exists(filePath)) {
                text = File.ReadAllText(filePath);
            }
            else {
                Console.WriteLine($"file {filePath} does not exist.");
                return;
            }
            //string file = args[]
            Console.WriteLine("C# Lexer test");
            Lexer lexer = new Lexer();
            List<Token> tokens = lexer.lexString(text);
            Utilities.TablePrinter table = new Utilities.TablePrinter("Token Value", "Token Type");
            foreach (Token token in tokens){
                string v = token.value.ToString().Replace("\n", "\\n");
                table.AddRow(v, token.type.ToString());
            }
            table.Print();

            new Interpreter();

            var t1 = Object.create(12L);
            var t2 = Object.create(13L);
            Console.WriteLine((t1 + t2).value);

            var l1 = Object.create(new List<object>{"1st element"});
            Console.WriteLine(l1[0]);
        }
    }
}
