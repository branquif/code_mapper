from antlr4 import *
from antlr.JavaLexer import JavaLexer
from antlr.JavaParser import JavaParser
from antlr.JavaParserVisitor import JavaParserVisitor
from java_code_parser_metadata import *
import sys

STRING_TYPE = 'String'
FILE_ENCODING = 'windows-1252'


class JavaParseTreeVisitor(JavaParserVisitor):
    def __init__(self):
        self.current_package = None
        self.imports = []
        self.reference_types = []
        self.current_modifiers = []
        self.scope_stack = []
        self.curr_type = None

    def visitPackageDeclaration(self, ctx: JavaParser.PackageDeclarationContext):
        self.current_package = ctx.qualifiedName().getText()
        self.visitChildren(ctx)
        # super().visitPackageDeclaration(ctx)

    def visitImportDeclaration(self, ctx: JavaParser.ImportDeclarationContext):
        self.imports.append(ctx.qualifiedName().getText())
        self.visitChildren(ctx)

    def visitTypeDeclaration(self, ctx: JavaParser.TypeDeclarationContext) -> None:
        curr_type = None
        if ctx.classDeclaration():
            self.curr_type = self.getReferenceTypeInfo(ctx.classDeclaration(), ReferenceType.CLASS)
            self.reference_types.append(curr_type)
        if ctx.interfaceDeclaration():
            self.curr_type = self.getReferenceTypeInfo(ctx.interfaceDeclaration(), ReferenceType.INTERFACE)
            self.reference_types.append(curr_type)
        if ctx.classOrInterfaceModifier():
            self.curr_type.annotations = self.getClassOrInterfaceAnnotations(ctx.classOrInterfaceModifier())
            pass
        if ctx.interfaceDeclaration():
            pass
        if ctx.enumDeclaration():
            pass
        if ctx.annotationTypeDeclaration():
            pass
        if ctx.recordDeclaration():
            pass

        self.visitChildren(ctx)

    def getReferenceTypeInfo(self,
                             ctx: JavaParser.ClassDeclarationContext | JavaParser.InterfaceDeclarationContext |
                                  JavaParser.RecordDeclarationContext | JavaParser.EnumDeclarationContext,
                             type: ReferenceType) -> (
            ReferenceTypeInfo):

        name = ctx.identifier().getText() if ctx else None
        line_number = ctx.start.line if ctx else None

        implements = []
        extends = []

        # handling extensions inheritances
        extends_ctx = ctx.EXTENDS()
        if extends_ctx:
            extend_types_ctx = ctx.typeList()
            for extend_type_ctx in extend_types_ctx:
                if type_ctx := extend_type_ctx.typeType()[0].classOrInterfaceType():
                    extend_name = type_ctx.typeIdentifier().getText()
                    generic_parameters = []
                    for parameter in type_ctx.typeArguments()[0].typeArgument():
                        generic_parameters.append(parameter.getText())
                    extends.append(InheritanceInfo(extend_name, generic_parameters))

        # handling implementation inheritances - valid only for classes
        if hasattr(ctx, "IMPLEMENTS"):
            implements_ctx = ctx.IMPLEMENTS()

            if implements_ctx:
                implements = [type_ctx.getText() for type_ctx in ctx.typeList().typeType()]

        return ReferenceTypeInfo(
            name=name,
            line_number=line_number,
            type=type,
            annotations=[],
            extends=extends,
            implements=implements,
            methods=[]
        )

    def visitClassBodyDeclaration(self, ctx: JavaParser.ClassBodyDeclarationContext):
        if member := ctx.memberDeclaration():
            self.current_modifiers = ctx.modifier()
            match member:
                case member if method_ctx := member.methodDeclaration():
                    method_info = self.getMethodInfo(method_ctx)
                    # process the method body to extract the string builders and string assignments
                    curr_type = self.reference_types[-1]
                    method_info.strings = self.filterMethod(method_ctx.methodBody().block())
                    curr_type.methods.append(method_info)

                case member if member.annotationTypeDeclaration():
                    pass
                case member if gen_method_ctx := member.genericMethodDeclaration():
                    method_info = self.getMethodInfo(gen_method_ctx.methodDeclaration())
                    # process the method body to extract the string builders and string assignments
                    curr_type = self.reference_types[-1]
                    method_info.strings = self.filterMethod(gen_method_ctx.methodDeclaration().methodBody().block())
                    curr_type.methods.append(method_info)

                case member if member.interfaceDeclaration():
                    pass
                case member if fieldDecl := member.fieldDeclaration():
                    field_info = self.getFieldInfo(fieldDecl)
                    curr_type = self.reference_types[-1]
                    curr_type.fields.append(field_info)
                case member if member.constructorDeclaration():
                    pass
                case member if member.classDeclaration():
                    pass

                case member if member.enumDeclaration():
                    pass
                case member if member.recordDeclaration():
                    pass

        self.visitChildren(ctx)

    def visitInterfaceBodyDeclaration(self, ctx: JavaParser.InterfaceBodyDeclarationContext):
        if member := ctx.interfaceMemberDeclaration():
            self.current_modifiers = ctx.modifier()
            match member:
                case member if member.interfaceMethodDeclaration():
                    method_info = self.getInterfaceMethodInfo(member.interfaceMethodDeclaration())
                    self.reference_types[-1].methods.append(method_info)
                case member if member.annotationTypeDeclaration():
                    pass
                case member if member.genericInterfaceMethodDeclaration():
                    method_info = self.getInterfaceMethodInfo(
                        member.genericInterfaceMethodDeclaration().methodDeclaration())
                    self.reference_types[-1].methods.append(method_info)
                case member if member.interfaceDeclaration():
                    pass
                case member if member.fieldDeclaration():
                    pass
                case member if member.constructorDeclaration():
                    pass
                case member if member.classDeclaration():
                    pass

                case member if member.enumDeclaration():
                    pass
                case member if member.recordDeclaration():
                    pass
                case member if member.constDeclaration():
                    pass

        self.visitChildren(ctx)

    def getFieldInfo(self, ctx: JavaParser.FieldDeclarationContext) -> FieldInfo:
        field_type = ctx.typeType().getText()
        line_number = ctx.start.line
        field_name = ctx.variableDeclarators().variableDeclarator()[0].variableDeclaratorId().getText()
        field_value = None
        if value := ctx.variableDeclarators().variableDeclarator()[0].variableInitializer():
            field_value = value.getText()
        annotations = self.getMethodAnnotations()

        return FieldInfo(
            name=field_name,
            line_number=line_number,
            type=field_type,
            value=field_value,
            annotations=annotations,
        )

    def getInterfaceMethodInfo(self, ctx: JavaParser.InterfaceMethodDeclarationContext) -> MethodInfo:
        # get the method name

        method_name = ctx.interfaceCommonBodyDeclaration().identifier().getText()
        line_number = ctx.start.line
        return_type = ctx.interfaceCommonBodyDeclaration().typeTypeOrVoid().getText()
        annotations = self.getMethodAnnotations()

        return MethodInfo(
            name=method_name,
            line_number=line_number,
            return_type=return_type,
            annotations=annotations,
        )

    def getMethodInfo(self, ctx: JavaParser.MethodDeclarationContext) -> MethodInfo:
        # get the method name
        method_name = ctx.identifier().getText()
        line_number = ctx.start.line
        return_type = ctx.typeTypeOrVoid().getText()
        annotations = self.getMethodAnnotations()

        return MethodInfo(
            name=method_name,
            line_number=line_number,
            return_type=return_type,
            annotations=annotations,
        )

    def getIterableElementValuePairs(self, pairs):
        return pairs if isinstance(pairs, list) else [pairs]

    def getClassOrInterfaceAnnotations(self, ctx: JavaParser.ClassOrInterfaceModifierContext) -> List[AnnotationInfo]:
        annotations = []
        for modifier in ctx:
            line_number = modifier.start.line
            annotation = modifier.annotation()
            if annotation:
                name = annotation.qualifiedName().getText()
                elementValuePairs = annotation.elementValuePairs()
                parameters = {}
                if elementValuePairs:
                    for elementPairs in self.getIterableElementValuePairs(elementValuePairs):
                        for pair in elementPairs.elementValuePair():
                            parameters[pair.identifier().getText()] = pair.elementValue().getText()
                annotations.append(AnnotationInfo(name=name, line_number=line_number, parameters=parameters))
        return annotations

    def getMethodAnnotations(self) -> List[AnnotationInfo]:
        annotations = []

        for modifier in self.current_modifiers:
            line_number = modifier.start.line
            annotation = modifier.classOrInterfaceModifier().annotation()
            if annotation:
                name = annotation.qualifiedName().getText()
                parameters = {}
                if annotation.elementValuePairs():
                    elementValuePairs = annotation.elementValuePairs()
                    if elementValuePairs:
                        for elementPairs in self.getIterableElementValuePairs(elementValuePairs):
                            for pair in elementPairs.elementValuePair():
                                parameters[pair.identifier().getText()] = pair.elementValue().getText()
                if annotation.elementValue():
                    parameters[name] = annotation.elementValue().getText()
                annotations.append(AnnotationInfo(name=name, line_number=line_number, parameters=parameters))
        return annotations

    def filterMethod(self, ctx: JavaParser.BlockContext) -> List[StringInfo]:
        interests = []
        if blkStatements := ctx.blockStatement():
            for blkStatement in blkStatements:
                match blkStatement:
                    case blkStatement if localVar := blkStatement.localVariableDeclaration():
                        if localVarDecl := localVar.variableDeclarators().variableDeclarator()[0]:
                            if type_ctx := localVar.typeType():
                                # it is a regular variable declaration
                                type = type_ctx.getText()
                                if type == 'String':
                                    name = localVarDecl.variableDeclaratorId().getText()
                                    line_number = blkStatement.start.line
                                    if localVarDecl.variableInitializer():
                                        value = localVarDecl.variableInitializer().getText()
                                    interests.append(StringInfo(name=name, content=value, line_number=line_number))
                            elif name := localVarDecl.identifier():
                                # it is a variable assignment
                                # check if there is a string in the expression text
                                value = localVarDecl.expression().getText()
                                if value.contains('"'):
                                    name = localVarDecl.identifier().getText()
                                    line_number = blkStatement.start.line
                                    type = None
                                    interests.append(StringInfo(name=name, content=value, line_number=line_number))


def main(file_path):
    input_stream = FileStream(file_path, encoding='windows-1252')
    lexer = JavaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = JavaParser(stream)
    tree = parser.compilationUnit()

    visitor = JavaParseTreeVisitor()
    visitor.visit(tree)

    java_file_info = JavaFileInfo(
        file_path=file_path,
        file_name=file_path.split('/')[-1],
        package_name=visitor.current_package,
        imports=visitor.imports,
        reference_types=visitor.reference_types
    )

    java_file_info.print_human_readable()


if __name__ == '__main__':
    path = (r'../../examples/Emissor NFE/EmissorNFe-master/EmissorNFeEJB/ejbModule/br/com/raiadrogasil/emissornfe'
            r'/business/NFeCompraIncorporacaoBusiness.java')

    # path = (
    #     r'../../examples/rd-estoque-master/estoque-model-impl/src/main/java/com/raiadrogasil/api/repository/type'
    #     r'/FilialMigradaEntity.java')

    # path = (
    #     r'../../examples/rd-estoque-master/estoque-repository-interface/src/main/java/com/raiadrogasil/api/repository'
    #     r'/type/query/EstoqueJpaRepository.java')
    main(path)
