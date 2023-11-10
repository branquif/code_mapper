from dataclasses import dataclass, field
from typing import List

@dataclass
class StringBuilderInfo:
    variable_name: str
    content: str
    line_number: int

@dataclass
class StringAssignmentInfo:
    variable_name: str
    content: str
    line_number: int

@dataclass
class MethodInfo:
    method_name: str
    scope_string_builders: List[StringBuilderInfo] = field(default_factory=list)
    string_assignments: List[StringAssignmentInfo] = field(default_factory=list)

@dataclass
class ClassInfo:
    class_name: str
    methods: List[MethodInfo] = field(default_factory=list)


from antlr4 import ParseTreeWalker
from pathlib import Path
from parser.JavaLexer import JavaLexer
from parser.JavaParser import JavaParser
from parser.JavaParserListener import JavaParserListener
from antlr4 import FileStream, CommonTokenStream


class MyJavaListener(JavaParserListener):

    def __init__(self):
        self.classes = []
        self.current_class = None
        self.current_method = None

    def enterClassDeclaration(self, ctx: JavaParser.ClassDeclarationContext):
        class_name = ctx.identifier().getText()
        self.current_class = ClassInfo(class_name)
        self.classes.append(self.current_class)

    def enterMethodDeclaration(self, ctx: JavaParser.MethodDeclarationContext):
        method_name = ctx.identifier().getText()
        self.current_method = MethodInfo(method_name)
        self.current_class.methods.append(self.current_method)

    def enterLocalVariableDeclaration(self, ctx: JavaParser.LocalVariableDeclarationContext):
        line_number = ctx.start.line
        variable_type = ctx.typeType().getText()

        if 'StringBuilder' in variable_type:
            var_name = ctx.variableDeclarators().variableDeclarator(0).variableDeclaratorId().identifier().getText()
            self.current_method.scope_string_builders.append(StringBuilderInfo(var_name, "", line_number))

        elif 'String' in variable_type:
            var_name = ctx.variableDeclarators().variableDeclarator(0).variableDeclaratorId().identifier().getText()
            initializer = ctx.variableDeclarators().variableDeclarator(0).variableInitializer()

            if initializer:
                content = initializer.getText().strip('"')
                self.current_method.string_assignments.append(StringAssignmentInfo(var_name, content, line_number))

    def enterExpression(self, ctx: JavaParser.ExpressionContext):
        if ctx.methodCall():
            method_name = ctx.methodCall().identifier().getText()
            if method_name == 'append':
                qualified_name = ctx.expression(0).getText()
                for sb in self.current_method.scope_string_builders:
                    if sb.variable_name == qualified_name:
                        args = ctx.methodCall().expressionList().expression()
                        for arg in args:
                            sb.content += arg.getText().strip('"')


file_path = Path(
    '../../examples/EmissorNFe-master/EmissorNFeEJB/ejbModule/br/com/raiadrogasil/emissornfe/business/NFeCompraIncorporacaoBusiness.java')
input_stream = FileStream(file_path, encoding='windows-1252')
lexer = JavaLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = JavaParser(token_stream)
tree = parser.compilationUnit()

listener = MyJavaListener()
walker = ParseTreeWalker()
walker.walk(listener, tree)

# Print the gathered info
for cls in listener.classes:
    print(f"Class: {cls.class_name}")
    for method in cls.methods:
        print(f"  Method: {method.method_name}")
        for sb in method.scope_string_builders:
            print(f"    StringBuilder: {sb.variable_name} (Line: {sb.line_number})")
            print(f"      Content: {sb.content}")
        for sa in method.string_assignments:
            print(f"    String Assignment: {sa.variable_name} (Line: {sa.line_number})")
            print(f"      Content: {sa.content}")
