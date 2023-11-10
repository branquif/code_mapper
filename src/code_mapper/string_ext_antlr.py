from antlr4 import *
from antlr.JavaLexer import JavaLexer
from antlr.JavaParser import JavaParser
from antlr.JavaParserVisitor import JavaParserVisitor
from dataclasses import dataclass, field
from typing import List
import sys


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
    extended_class: str = None
    implemented_interfaces: List[str] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)


@dataclass
class JavaFileInfo:
    package_name: str
    imports: List[str] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

    def print_human_readable(self):
        print(f"Package: {self.package_name}")
        print(f"Imports: {', '.join(self.imports)}")
        for cls in self.classes:
            print(f"Class: {cls.class_name}")
            if cls.extended_class:
                print(f"  Extends: {cls.extended_class}")
            if cls.implemented_interfaces:
                print(f"  Implements: {', '.join(cls.implemented_interfaces)}")
            print("  Methods:")
            for method in cls.methods:
                print(f"    {method.method_name}")
                for sb in method.scope_string_builders:
                    print(f"      StringBuilder: {sb.variable_name} - Content: {sb.content} - Line: {sb.line_number}")
                for sa in method.string_assignments:
                    print(
                        f"      String Assignment: {sa.variable_name} - Content: {sa.content} - Line: {sa.line_number}")


class JavaParseTreeVisitor(JavaParserVisitor):
    def __init__(self):
        self.current_package = None
        self.imports = []
        self.classes = []

    def visitPackageDeclaration(self, ctx: JavaParser.PackageDeclarationContext):
        self.current_package = ctx.qualifiedName().getText()

    def visitImportDeclaration(self, ctx: JavaParser.ImportDeclarationContext):
        self.imports.append(ctx.qualifiedName().getText())

    def visitClassDeclaration(self, ctx: JavaParser.ClassDeclarationContext):
        class_name_ctx = next((child for child in ctx.children if isinstance(child, JavaParser.IdentifierContext)),
                              None)
        class_name = class_name_ctx.getText() if class_name_ctx else None
        extended_class = None
        implemented_interfaces = []

        # Handling inheritance
        extends_ctx = ctx.EXTENDS()
        if extends_ctx:
            extended_class = ctx.typeType().getText()  # Assuming there's always only one class to extend

        # Handling interfaces
        implements_ctx = ctx.IMPLEMENTS()
        if implements_ctx:
            implemented_interfaces = [type_ctx.getText() for type_ctx in ctx.typeList().typeType()]

        class_info = ClassInfo(
            class_name=class_name,
            extended_class=extended_class,
            implemented_interfaces=implemented_interfaces,
            methods=[]
        )
        self.classes.append(class_info)

        return self.visitChildren(ctx)

    # The rest of the visitor's methods
    # ...


def main(file_path):
    try:
        input_stream = FileStream(file_path, encoding='windows-1252')
        lexer = JavaLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = JavaParser(stream)
        tree = parser.compilationUnit()

        visitor = JavaParseTreeVisitor()
        visitor.visit(tree)

        java_file_info = JavaFileInfo(
            package_name=visitor.current_package,
            imports=visitor.imports,
            classes=visitor.classes
        )

        java_file_info.print_human_readable()

    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)


if __name__ == '__main__':
    path = r'../../examples/Emissor NFE/EmissorNFe-master/EmissorNFeEJB/ejbModule/br/com/raiadrogasil/emissornfe/business/NFeCompraIncorporacaoBusiness.java'
    main(path)
