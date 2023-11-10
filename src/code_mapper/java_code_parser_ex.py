from antlr4 import *
from antlr.JavaLexer import JavaLexer
from antlr.JavaParser import JavaParser
from antlr.JavaParserVisitor import JavaParserVisitor
from java_code_parser_metadata import *
from pathlib import Path
import re

STRING_TYPE = 'String'
FILE_ENCODING = 'windows-1252'

# regex patterns to extract objects and methods from a string
object_pattern = re.compile(r'^(\w+)')
method_pattern = re.compile(r'(\.\w+\(.*?\))')


class JavaParseTreeVisitor(JavaParserVisitor):
    def __init__(self):
        self.current_package = None
        self.imports = []
        self.reference_types = []
        self.current_modifiers = []
        self.current_type = None
        self.current_method = None
        self.current_annotations = []
        self.global_scope = Scope()  # the global scope of the file
        self.current_scope = self.global_scope  # the current scope.
        # self.current_scope_idx = -1

    def visitPackageDeclaration(self, ctx: JavaParser.PackageDeclarationContext):
        self.current_package = ctx.qualifiedName().getText()
        self.visitChildren(ctx)

    def visitImportDeclaration(self, ctx: JavaParser.ImportDeclarationContext):
        self.imports.append(ctx.qualifiedName().getText())
        self.visitChildren(ctx)

    def get_iterable_element(self, pairs):
        return pairs if isinstance(pairs, list) else [pairs]

    def get_annotation_info(self, ctx: JavaParser.AnnotationContext):
        name = ctx.qualifiedName().getText()
        line_number = ctx.start.line
        parameters = {}
        if ctx.elementValuePairs():
            elementValuePairs = ctx.elementValuePairs()
            if elementValuePairs:
                for elementPairs in self.get_iterable_element(elementValuePairs):
                    for pair in elementPairs.elementValuePair():
                        parameters[pair.identifier().getText()] = pair.elementValue().getText()
        if ctx.elementValue():
            parameters[name] = ctx.elementValue().getText()
        return AnnotationInfo(name=name, line_number=line_number, parameters=parameters)

    def visitClassOrInterfaceModifier(self, ctx: JavaParser.ClassOrInterfaceModifierContext):
        # this visitor is called for every modifier in the class or interface declaration
        # and comes before their declaration in the parse tree
        if annotation_ctx := ctx.annotation():  # just process annotations
            self.current_annotations.append(self.get_annotation_info(annotation_ctx))
        self.visitChildren(ctx)

    def visitClassDeclaration(self, ctx: JavaParser.ClassDeclarationContext):
        self.current_type = self.get_reference_type_info(ctx, ReferenceType.CLASS)
        if self.current_annotations:
            self.current_type.annotations = self.current_annotations
            self.current_annotations = []
        self.reference_types.append(self.current_type)
        self.visitChildren(ctx)

    def visitInterfaceDeclaration(self, ctx: JavaParser.InterfaceDeclarationContext):
        self.current_type = self.get_reference_type_info(ctx, ReferenceType.INTERFACE)
        if self.current_annotations:
            self.current_type.annotations = self.current_annotations
            self.current_annotations = []
        self.reference_types.append(self.current_type)
        self.visitChildren(ctx)

    def get_reference_type_info(self,
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

    def get_attributes_from_modifiers(self,
                                      ctx: JavaParser.ClassBodyDeclarationContext |
                                           JavaParser.InterfaceBodyDeclarationContext) -> None:
        if modifiers := ctx.modifier():
            self.current_annotations = []
            for modifier in modifiers:
                if annotation_ctx := modifier.classOrInterfaceModifier().annotation():
                    self.current_annotations.append(self.get_annotation_info(annotation_ctx))

    def visitClassBodyDeclaration(self, ctx: JavaParser.ClassBodyDeclarationContext) -> None:
        # need to visit the ClassBodyDeclaration to get the modifiers, which contains the annotations
        self.get_attributes_from_modifiers(ctx)
        self.current_annotations = []
        self.visitChildren(ctx)

    def visitInterfaceBodyDeclaration(self, ctx: JavaParser.InterfaceBodyDeclarationContext) -> None:
        self.get_attributes_from_modifiers(ctx)
        self.current_annotations = []
        self.visitChildren(ctx)

    def visitFieldDeclaration(self, ctx: JavaParser.FieldDeclarationContext) -> None:
        field_value = None
        if value := ctx.variableDeclarators().variableDeclarator()[0].variableInitializer():
            field_value = value.getText()
        self.current_type.fields.append(FieldInfo(
            name=ctx.variableDeclarators().variableDeclarator()[0].variableDeclaratorId().getText(),
            line_number=ctx.start.line,
            type=ctx.typeType().getText(),
            value=field_value,
            annotations=self.current_annotations
        ))
        self.current_annotations = []  # reset the annotations
        self.visitChildren(ctx)

    def visitInterfaceMethodDeclaration(self, ctx: JavaParser.InterfaceMethodDeclarationContext) -> None:
        self.current_type.methods.append(MethodInfo(
            name=ctx.interfaceCommonBodyDeclaration().identifier().getText(),
            line_number=ctx.start.line,
            return_type=ctx.interfaceCommonBodyDeclaration().typeTypeOrVoid().getText(),
            annotations=self.current_annotations
        ))
        self.current_annotations = []  # reset the annotations
        self.visitChildren(ctx)

    def process_method_declaration(self,
                                   ctx: JavaParser.MethodDeclarationContext | JavaParser.ConstructorDeclarationContext,
                                   isConstructor: bool = False):
        self.current_method = MethodInfo(
            name=ctx.identifier().getText(),
            line_number=ctx.start.line,
            return_type='' if isConstructor else ctx.typeTypeOrVoid().getText(),
            annotations=self.current_annotations
        )
        self.current_annotations = []  # reset the annotations
        self.visitChildren(ctx)
        self.current_method.scope = self.current_scope.children[-1]
        # prune emtpy scopes
        if self.current_method.scope.is_empty():
            self.current_method.scope = None
        self.current_type.methods.append(self.current_method)

    def visitConstructorDeclaration(self, ctx: JavaParser.ConstructorDeclarationContext) -> None:
        self.process_method_declaration(ctx, True)

    def visitMethodDeclaration(self, ctx: JavaParser.MethodDeclarationContext) -> None:
        self.process_method_declaration(ctx, False)

    def visitBlock(self, ctx: JavaParser.BlockContext) -> None:
        # Create a new scope with the current one as its parent
        new_scope = Scope(parent=self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        # process children
        self.visitChildren(ctx)
        self.current_scope = self.current_scope.parent
        pass

    def visitLocalVariableDeclaration(self, ctx: JavaParser.LocalVariableDeclarationContext) -> None:
        type_ctx = ctx.typeType()
        # process objects of interest
        if type_ctx.classOrInterfaceType() and ObjectType.type_of_interest(type_ctx.classOrInterfaceType().getText()):
            for declarator_ctx in ctx.variableDeclarators().variableDeclarator():
                obj_name = declarator_ctx.variableDeclaratorId().getText()
                obj_type = ObjectType(type_ctx.classOrInterfaceType().getText())
                line_number = declarator_ctx.start.line
                new_expression_info = ExpressionInfo(
                    name=obj_name,
                    line_number=line_number,
                    type=obj_type,
                    expression_type=ExpressionType.OBJECT_CREATION,
                    content=''
                )
                match obj_type:
                    case ObjectType.STRING:
                        new_expression_info.content = declarator_ctx.variableInitializer().getText()
                        pass
                    case ObjectType.STRING_BUILDER:
                        pass

                self.current_scope.expressions.append({obj_name: new_expression_info})
                self.visitChildren(ctx)

    def visitExpression(self, ctx: JavaParser.ExpressionContext) -> None:
        # get the variable assignment to a new object of interest
        if ctx.ASSIGN() and ctx.expression(1).NEW():
            # the code is reusing a variable to create a new object
            # get the object name
            obj_name = ctx.expression(0).getText()
            # get the object type
            obj_type_name = ctx.expression(1).children[1].createdName().getText()
            if ObjectType.type_of_interest(obj_type_name):
                obj_type = ObjectType(obj_type_name)
                line_number = ctx.start.line
                new_expression_info = ExpressionInfo(
                    name=obj_name,
                    line_number=line_number,
                    type=obj_type,
                    expression_type=ExpressionType.OBJECT_CREATION,
                    content=''
                )

                self.current_scope.expressions.append({obj_name: new_expression_info})
        self.visitChildren(ctx)


    def visitMethodCall(self, ctx: JavaParser.MethodCallContext):
        # get the method name
        method_name = ctx.identifier().getText()
        if method_name in METHODS_OF_INTEREST:
            # get object from parent context
            object_name = ctx.parentCtx.expression(0).getText()
            # check if the object name is within the scope
            scope = self.current_scope.get_object_scope(object_name)
            if scope:
                parameter_values = ctx.arguments().getText()
                expression = scope.get_expression_by_name(object_name)

                expression.method_calls.append(ExpressionInfo(
                    name=method_name,
                    line_number=ctx.start.line,
                    type=expression.type,
                    expression_type=ExpressionType.METHOD_CALL,
                    content=parameter_values
                ))
        self.visitChildren(ctx)


def main(file_path: Path):
    input_stream = FileStream(file_path, encoding='windows-1252')
    lexer = JavaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = JavaParser(stream)
    tree = parser.compilationUnit()

    visitor = JavaParseTreeVisitor()
    visitor.visit(tree)

    java_file_info = JavaFileInfo(
        file_path=str(file_path.parent),
        file_name=file_path.name,
        package_name=visitor.current_package,
        imports=visitor.imports,
        reference_types=visitor.reference_types
    )

    java_file_info.print_human_readable()


if __name__ == '__main__':
    # path = Path(r'../../examples/Emissor NFE/EmissorNFe-master/EmissorNFeEJB/ejbModule/br/com/raiadrogasil/emissornfe'
    #             r'/business/NFeCompraIncorporacaoBusiness.java')

    path = Path(r'../../examples/FaturaDAO.java')

    # path = Path(
    #     r'../../examples/rd-estoque-master/estoque-model-impl/src/main/java/com/raiadrogasil/api/repository/type'
    #     r'/FilialMigradaEntity.java')

    # path = Path(
    #     r'../../examples/rd-estoque-master/estoque-repository-interface/src/main/java/com/raiadrogasil/api/repository'
    #     r'/type/query/EstoqueJpaRepository.java')
    main(path)
