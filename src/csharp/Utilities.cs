using System.Collections.Generic;
using System.Reflection;
using System.Linq;
using System;

namespace Utilities
{
    public class Utilities {
        public static Type[] GetInheritedClasses(Type MyType) 
        {
        	return Assembly.GetAssembly(MyType).GetTypes().Where(TheType => TheType.IsClass && !TheType.IsAbstract && TheType.IsSubclassOf(MyType)).ToArray();
        }
    }
    public class TablePrinter
    {
        // https://stackoverflow.com/a/54943087
        private readonly string[] titles;
        private readonly List<int> lengths;
        private readonly List<string[]> rows = new List<string[]>();

        public TablePrinter(params string[] titles)
        {
            this.titles = titles;
            lengths = titles.Select(t => t.Length).ToList();
        }

        public void AddRow(params object[] row)
        {
            if (row.Length != titles.Length)
            {
                throw new System.Exception($"Added row length [{row.Length}] is not equal to title row length [{titles.Length}]");
            }
            rows.Add(row.Select(o => o.ToString()).ToArray());
            for (int i = 0; i < titles.Length; i++)
            {
                if (rows.Last()[i].Length > lengths[i])
                {
                    lengths[i] = rows.Last()[i].Length;
                }
            }
        }

        public void Print()
        {
            lengths.ForEach(l => System.Console.Write("+-" + new string('-', l) + '-'));
            System.Console.WriteLine("+");

            string line = "";
            for (int i = 0; i < titles.Length; i++)
            {
                line += "| " + titles[i].PadRight(lengths[i]) + ' ';
            }
            System.Console.WriteLine(line + "|");

            lengths.ForEach(l => System.Console.Write("+-" + new string('-', l) + '-'));
            System.Console.WriteLine("+");

            foreach (var row in rows)
            {
                line = "";
                for (int i = 0; i < row.Length; i++)
                {
                    if (int.TryParse(row[i], out int n))
                    {
                        line += "| " + row[i].PadLeft(lengths[i]) + ' ';  // numbers are padded to the left
                    }
                    else
                    {
                        line += "| " + row[i].PadRight(lengths[i]) + ' ';
                    }
                }
                System.Console.WriteLine(line + "|");
            }

            lengths.ForEach(l => System.Console.Write("+-" + new string('-', l) + '-'));
            System.Console.WriteLine("+");
        }
    }

    public class Tracker {
        public Dictionary<string, Dictionary<int, object>> values;
        public int line;
        public bool compact;
        public List<string> variables;
        public Tracker(List<string> variables, bool compact=false){
            this.values = new Dictionary<string, Dictionary<int, object>>{};
            this.line = 0;
            this.compact = compact;
            this.variables = variables;
        }
        
        public void onchange(string name, object value){
            //Console.WriteLine($"change '{name}' to {value}");
            if (variables.Contains(name)){
                Dictionary<int, object> data;
                if (!values.TryGetValue(name, out data)) data = new Dictionary<int, object>{};
                
                
                if (data.TryGetValue(line, out var temp) || !compact){
                    line += 1;
                }
                
                data[line] = value;
        
                values[name] = data;
            }
        }
        public void displayTraceTable(List<string> variables){
            var headers = values.Keys.ToList();
            if (variables.Count > 0) headers = variables;
            
            int maxLine = 0;
            foreach (var v in values.Values){
                foreach (var line in v.Keys){
                    if (line > maxLine){
                        maxLine = line;
                    }
                }
            }
            
            
            var table = new TablePrinter(headers.ToArray());
            Console.WriteLine($"maxline: {maxLine}");
            for (int i = 0; i < maxLine+1; i++){
                List<object> row = new List<object>{};
                foreach (var h in headers){
                    if (values.TryGetValue(h, out var t1)){
                        if (t1.TryGetValue(i, out var t2)){
                            row.Add(t2);
                            continue;
                        }
                    }
                    row.Add("");
                    
                }
                table.AddRow(row.ToArray());
            }
            table.Print();
        }
    }
}