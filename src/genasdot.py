from lexer import *
from parse import *
import argparse
import textwrap
from traceback import print_exc

class DotGenerator(NodeVisitor):
    def __init__(self, parser: Parser, shape="circle"):
        global __interpreter__
        self.parser = parser
        self.ncount = 0
        self.dot_header = [textwrap.dedent("""\
        digraph astgraph {
          node [shape="""+shape+""", fontsize=12, fontname="Courier", height=.1];
          ranksep=.3;
          edge [arrowsize=.5]
        """)]

        self.dot_body = []
        self.dot_footer = ['}']

        self.visit_IntObject = self.visit_FloatObject = self.visit_StringObject = self.visit_BoolObject = self.visit_Object

        __interpreter__ = self
    
    def addNode(self, s=None, *format_params):
        string = (s if s != None else '  node{} [label="{}"]\n').format(*format_params)
        self.dot_body.append(string)
    
    def link(self, n1, n2):
        self.dot_body.append('  node{} -> node{}\n'.format(n1, n2))
    
    def visit_Compound(self, node: Compound):
        self.addNode(None, self.ncount, "Compound")
        node._num = self.ncount
        self.ncount += 1
        
        for child in node.children:
            self.visit(child)
            self.link(node._num, child._num)
    
    def visit_Assign(self, node: Assign):
        self.visit_BinOp(node)
    
    def visit_Var(self, node: Var):
        self.addNode(None, self.ncount, node.value)
        node._num = self.ncount
        self.ncount += 1

        for p in node.array_indexes:
            self.addNode(None, self.ncount, "Property")
            self.link(node._num, self.ncount)
            property_num = self.ncount
            self.ncount += 1
            self.visit(p)
            self.link(property_num, p._num)
            
            
    
    def visit_BinOp(self, node: BinOp):
        self.addNode(None, self.ncount, node.op.value)
        node._num = self.ncount
        self.ncount += 1

        for child_node in (node.left, node.right):
            self.visit(child_node)
            self.link(node._num, child_node._num)
    
    def visit_UnaryOp(self, node: UnaryOp):
        self.addNode(None, self.ncount, "unary " + node.op.value)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.expr)
        self.link(node._num, node.expr._num)
    
    def visit_Object(self, node: Object):
        self.addNode(None, self.ncount, repr(node.value))
        node._num = self.ncount
        self.ncount += 1
    
    def visit_ArrayObject(self, node: ArrayObject):
        self.addNode(None, self.ncount, "ArrayObject")
        node._num = self.ncount
        self.ncount += 1

        for item in node.value:
            self.visit(item)
            self.link(node._num, item._num)
    
    def visit_DeclaredParam(self, node: DeclaredParam):
        self.addNode(None, self.ncount, "Param")
        node._num = self.ncount
        self.ncount += 1
        
        self.visit(node.variable)
        self.link(node._num, node.variable._num)
    
    def visit_Param(self, node: Param):
        self.addNode(None, self.ncount, "Param")
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.value)
        self.link(node._num, node.value._num)


    def visit_Subroutine(self, node: Subroutine):
        self.addNode(
            '  node{} [label="Subroutine:{}"]\n',
            self.ncount,
            node.token.value
        )
        node._num = self.ncount
        self.ncount += 1

        for param_node in node.parameters:
            self.visit(param_node)
            self.link(node._num, param_node._num)
        
        self.visit(node.compound)
        self.link(node._num, node.compound._num)
    
    def visit_SubroutineCall(self, node: SubroutineCall):
        self.addNode(None, self.ncount, "SubroutineCall")
        node._num = self.ncount
        self.ncount += 1

        self.addNode(None, self.ncount, "Target")
        self.link(node._num, self.ncount)
        t_num = self.ncount
        self.ncount += 1

        self.visit(node.subroutine_token)
        self.link(t_num, node.subroutine_token._num)


        for param_node in node.parameters:
            self.visit(param_node)
            self.link(node._num, param_node._num)
    
    def visit_Record(self, node: Record):
        self.addNode('  node{} [label="Record:{}"]\n', self.ncount, node.token.value)
        node._num = self.ncount
        self.ncount += 1
        
        for p in node.parameters:
            self.addNode(None, self.ncount, p)
            _num = self.ncount
            self.ncount += 1
            
            self.link(node._num, _num)
    
    def visit_ClassDefinition(self, node: ClassDefinition):
        self.addNode('  node{} [label="ClassDefinition:{}"]\n', self.ncount, node.token.value)
        node._num = self.ncount
        self.ncount += 1

        for v in node.static_values:
            self.visit(v)
            self.link(node._num, v._num)
        
        for subroutine in node.subroutines:
            self.visit(subroutine)
            self.link(node._num, subroutine._num)
    
    def visit_Magic(self, node: Magic):
        self.addNode('  node{} [label="Magic:{}"]\n', self.ncount, node.token.value)
        node._num = self.ncount
        self.ncount += 1

        for param_node in node.parameters:
            self.visit(param_node)
            self.link(node._num, param_node._num)
    
    def visit_IfStatement(self, node: IfStatement):
        self.addNode(None, self.ncount, "IfStatement")
        node._num = self.ncount
        self.ncount += 1

        self.addNode(None, self.ncount, "Condition")
        self.link(node._num, self.ncount)
        condition_num = self.ncount
        self.ncount += 1

        self.visit(node.condition)
        self.link(condition_num, node.condition._num)

        self.addNode(None, self.ncount, "Consequence")
        self.link(node._num, self.ncount)
        consequence_num = self.ncount
        self.ncount += 1

        self.visit(node.consequence)
        self.link(consequence_num, node.consequence._num)

        self.addNode(None, self.ncount, "Alternatives")
        self.link(node._num, self.ncount)
        alternatives_num = self.ncount
        self.ncount += 1
        
        for statement in node.alternatives:
            self.visit(statement)
            self.link(alternatives_num, statement._num)
    
    def visit_WhileStatement(self, node: WhileStatement, isRepeatUntilStatement=False):
        name = "RepeatUntil" if isRepeatUntilStatement else "While"
        self.addNode(None, self.ncount, name+"Statement")
        node._num = self.ncount
        self.ncount += 1

        self.addNode(None, self.ncount, "Condition")
        self.link(node._num, self.ncount)
        condition_num = self.ncount
        self.ncount += 1

        self.visit(node.condition)
        self.link(condition_num, node.condition._num)

        self.addNode(None, self.ncount, "Consequence")
        self.link(node._num, self.ncount)
        consequence_num = self.ncount
        self.ncount += 1

        self.visit(node.consequence)
        self.link(consequence_num, node.consequence._num)
    
    def visit_RepeatUntilStatement(self, node: RepeatUntilStatement):
        self.visit_WhileStatement(node, True)
    
    def visit_ForLoop(self, node: ForLoop):
        self.addNode(None, self.ncount, "ForLoop")
        node._num = self.ncount
        self.ncount += 1

        self.addNode(None, self.ncount, "Variable")
        self.link(node._num, self.ncount)
        var_num = self.ncount
        self.ncount += 1

        self.visit(node.variable)
        self.link(var_num, node.variable._num)

        if node.to_step:
            self.addNode(None, self.ncount, "Start")
            self.link(node._num, self.ncount)
            start_num = self.ncount
            self.ncount += 1

            self.visit(node.start)

            self.link(start_num, node.start._num)

            self.addNode(None, self.ncount, "End")
            self.link(node._num, self.ncount)
            end_num = self.ncount
            self.ncount += 1

            self.visit(node.end)

            self.link(end_num, node.end._num)

            if node.step:
                self.addNode(None, self.ncount, "Step")
                self.link(node._num, self.ncount)
                step_num = self.ncount
                self.ncount += 1

                self.visit(node.step)

                self.link(step_num, node.step._num)
        else:
            self.addNode(None, self.ncount, "Iterator")
            self.link(node._num, self.ncount)
            iterator_num = self.ncount
            self.ncount += 1

            self.visit(node.iterator)
            self.link(iterator_num, node.iterator._num)

        
        self.addNode(None, self.ncount, "Loop")
        self.link(node._num, self.ncount)
        loop_num = self.ncount
        self.ncount += 1
        self.visit(node.loop)
        self.link(loop_num, node.loop._num)
    
    def visit_TryCatch(self, node: TryCatch):
        self.addNode(None, self.ncount, "TryCatch")
        node._num = self.ncount
        self.ncount += 1

        self.addNode(None, self.ncount, "Try")
        _num = self.ncount
        self.link(node._num, _num)
        self.ncount += 1
        self.visit(node.try_compound)
        self.link(_num, node.try_compound._num)
    
        self.addNode(None, self.ncount, "Catch")
        _num = self.ncount
        self.link(node._num, _num)
        self.ncount += 1
        self.visit(node.catch_compound)
        self.link(_num, node.catch_compound._num)
    
    def visit_NoOp(self, node: NoOp):
        self.addNode(None, self.ncount, "NoOp")
        node._num = self.ncount
        self.ncount += 1
    
    def generate(self):
        tree = self.parser.parse()
        self.visit(tree)

        return ''.join(self.dot_header + self.dot_body + self.dot_footer)



parser = argparse.ArgumentParser(description="Dot file generator")
parser.add_argument("inputfile", type=argparse.FileType("r", encoding="utf-8"), nargs="?")
parser.add_argument("-c", nargs="?")
parser.add_argument("--shape", action="store", dest="shape")

options = parser.parse_args()
#print(options)
if options.inputfile:
    string = options.inputfile.read()
    options.inputfile.close()
else:
    string = options.c

l = Lexer()
result = l.lexString(string)
p = Parser(l)
i = DotGenerator(p, shape=options.shape if options.shape else "circle")
string = i.generate()
print(string)

# Example:
# python genasdot.py -c "OUTPUT 2 + 3 * 4" > ast.dot && dot -Tpng -o ast.png ast.dot
# python genasdot.py ..\examples\sieve.ecp > ast.dot && dot -Tpng -o ast.png ast.dot
    