# this code works like a charm!

from dataclasses import dataclass
from typing import List
from pathlib import Path
import javalang


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
    scope_string_builders: List[StringBuilderInfo]
    string_assignments: List[StringAssignmentInfo]


@dataclass
class ClassInfo:
    class_name: str
    inheritance: List[str]
    methods: List[MethodInfo]


@dataclass
class JavaFileInfo:
    package: str
    classes: List[ClassInfo]


def pretty_print_java_info(java_info: JavaFileInfo):
    print(f"Package: {java_info.package}\n")
    for cls in java_info.classes:
        print(f"Class: {cls.class_name}")
        print(f"  Inherits/Implements: {', '.join(cls.inheritance) if cls.inheritance else 'None'}")

        for method in cls.methods:
            print(f"  - Method: {method.method_name}")
            for sb_info in method.scope_string_builders:
                print(f"    * StringBuilder Variable: {sb_info.variable_name} (Line: {sb_info.line_number})")
                print(f"      Content: {sb_info.content}")

            for sa_info in method.string_assignments:
                print(f"    * String Assignment: {sa_info.variable_name} (Line: {sa_info.line_number})")
                print(f"      Content: {sa_info.content}")
        print()


def parse_java_file(code: str) -> JavaFileInfo:
    tree = javalang.parse.parse(code)

    package = tree.package.name if tree.package else ""
    classes = []

    for _, class_decl in tree.filter(javalang.tree.ClassDeclaration):
        inheritance = (class_decl.implements if class_decl.implements else []) + (
            [class_decl.extends.name] if class_decl.extends else [])
        methods = []

        for _, method_decl in class_decl.filter(javalang.tree.MethodDeclaration):
            method_name = method_decl.name
            scope_string_builders = []
            string_assignments = []

            for path, statement in method_decl.filter(javalang.tree.LocalVariableDeclaration):
                line_number = statement._position.line

                if 'StringBuilder' in statement.type.name:
                    for declarator in statement.declarators:
                        variable_name = declarator.name
                        string_content = ""
                        sb_info = StringBuilderInfo(variable_name, string_content, line_number)
                        scope_string_builders.append(sb_info)

                elif 'String' in statement.type.name:
                    for declarator in statement.declarators:
                        variable_name = declarator.name
                        if declarator.initializer:
                            content = ""
                            for _, part in declarator.initializer.filter(javalang.tree.Literal):
                                content += part.value.replace('"', '')
                            string_assignments.append(StringAssignmentInfo(variable_name, content, line_number))

            for p, expr in method_decl.filter(javalang.tree.MethodInvocation):
                line_number = expr._position.line

                for sb_info in scope_string_builders:
                    if expr.qualifier == sb_info.variable_name and expr.member == 'append':
                        first_argument = expr.arguments[0]
                        if isinstance(first_argument, javalang.tree.Literal):
                            sb_info.content += first_argument.value.replace('"', '')

            # Only include the method if it contains String or StringBuilder instances
            if scope_string_builders or string_assignments:
                methods.append(MethodInfo(method_name, scope_string_builders, string_assignments))

        classes.append(ClassInfo(class_decl.name, inheritance, methods))

    return JavaFileInfo(package, classes)

if __name__ == '__main__':
    file_path = Path(
        '../../examples/EmissorNFe-master/EmissorNFeEJB/ejbModule/br/com/raiadrogasil/emissornfe/business/NFeTransferenciaCDImprioLojaAjusteBusiness.java')
    with open(file_path, 'r', encoding='windows-1252') as f:
        code_content = f.read()

    result = parse_java_file(code_content)
    pretty_print_java_info(result)
