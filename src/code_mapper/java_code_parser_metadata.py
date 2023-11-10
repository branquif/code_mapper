from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import List, Dict, Optional, Union

MODIFY_DATA_METHODS = {'save', 'saveAll', 'flush'
                                          'delete', 'deleteByIs', 'deleteAllByIs',
                       'deleteAllByIsIn', 'deleteAllByIsNotIn',
                       'deleteInBatch', 'deleteInAllBatch'}

QUERY_DATA_METHODS = {'findById', 'findByIds', 'findByIdIn', 'findByIdNotIn',
                      'findAll', 'findAllById', 'findAllByIdIn', 'findAllByIdNotIn',
                      'findAllByIs', 'findAllByIsIn', 'findAllByIsNotIn',
                      'findAllByIsOrderBy', 'findAllByIsInOrderBy', 'findAllByIsNotInOrderBy',
                      'findAllByIsOrderByDesc', 'findAllByIsInOrderByDesc', 'findAllByIsNotInOrderByDesc',
                      'findAllByIsOrderByAsc', 'findAllByIsInOrderByAsc', 'findAllByIsNotInOrderByAsc',
                      'findAllByIsNot', 'findAllByIsNotIn',
                      'findAllByIsNotOrderBy', 'findAllByIsNotInOrderBy',
                      'findAllByIsNotOrderByDesc', 'findAllByIsNotInOrderByDesc',
                      'findAllByIsNotOrderByAsc', 'findAllByIsNotInOrderByAsc',
                      'findAllByIsNotAndIsNot', 'findAllByIsNotInAndIsNotIn',
                      'findAllByIsNotAndIsNotOrderBy', 'findAllByIsNotInAndIsNotInOrderBy',
                      'findAllByIsNotAndIsNotOrderByDesc', 'findAllByIsNotInAndIsNotInOrderByDesc',
                      'findAllByIsNotAndIsNotOrderByAsc', 'findAllByIsNotInAndIsNotInOrderByAsc',
                      'findAllByIsNotAndIsNotAndIsNot', 'findAllByIsNotInAndIsNotInAndIsNotIn',
                      'findAllByIsNotAndIsNotAndIsNotOrderBy', 'findAllByIsNotInAndIsNotInAndIsNotInOrderBy',
                      'findAllByIsNotAndIsNotAndIsNotOrderByDesc', 'findAllByIsNotInAndIsNotInAndIsNotInOrderByDesc',
                      'findAllByIsNotAndIsNotAndIsNotOrderByAsc', 'findAllByIsNotInAndIsNotInAndIsNotInOrderByAsc',
                      'findAllByIsNotAndIsNotAndIsNotAndIsNot', 'findAllByIsNotInAndIsNotInAndIsNotInAndIsNotIn',
                      'findAllByIsNotAndIsNotAndIsNotAndIsNotOrderBy',
                      'findAllByIsNotInAndIsNotInAndIsNotInAndIsNotInOrderBy',
                      'findAllByIsNotAndIsNotAndIsNotAndIsNotOrderByDesc',
                      'findAllByIsNotInAndIsNotInAndIsNotInAndIsNot',
                      'existsById', 'existsByIdIn', 'existsByIdNotIn',
                      'count', 'countById', 'countByIdIn', 'countByIdNotIn',
                      'countByIs', 'countByIsIn', 'countByIsNotIn',
                      'countByIsNot', 'countByIsNotIn',
                      'existsById', 'existsByIdIn', 'existsByIdNotIn',
                      'existsByIs', 'existsByIsIn', 'existsByIsNotIn'}

METHODS_OF_INTEREST = {'append'} | MODIFY_DATA_METHODS | QUERY_DATA_METHODS

QUERY_ANNOTATIONS = {'@Query', '@NamedQuery', '@NamedNativeQuery'}
CALL_ANNOTATIONS = {'@Procedure', '@Function', '@NamedStoredProcedureQuery', '@NamedStoredProcedureQueries'}
MODIFY_ANNOTATIONS = {'@Modifying', '@Transactional', '@TransactionalEventListener',
                      '@TransactionalEventListenerFactory'}
ENTITY_ANNOTATIONS = {'@Entity', '@Embeddable', '@MappedSuperclass', '@Table', '@SecondaryTable', '@SecondaryTables',
                      '@Inheritance', '@DiscriminatorColumn', '@DiscriminatorValue', '@ExcludeDefaultListeners',
                      '@ExcludeSuperclassListeners', '@EntityListeners', '@EntityResult', '@FieldResult',
                      '@ConstructorResult', '@SqlResultSetMapping', '@NamedEntityGraph', '@NamedEntityGraphs',
                      '@NamedAttributeNode', '@NamedSubgraph', '@NamedSubgraphs', '@NamedNativeQueries',
                      '@NamedNativeQuery', '@NamedQueries', '@NamedQuery', '@SqlResultSetMappings',
                      '@SqlResultSetMapping', '@Convert', '@Converter', '@Converts', '@Version', '@Id', '@EmbeddedId',
                      '@GeneratedValue', '@Column', '@Temporal', '@Enumerated', '@Lob', '@Basic', '@Transient',
                      '@Access', '@Embedded', '@ElementCollection', '@CollectionTable', '@MapKeyColumn', '@MapKeyClass',
                      '@MapKeyTemporal', '@MapKeyEnumerated', '@MapKeyLob', '@MapKeyBasic', '@OrderColumn',
                      '@OrderColumn', '@AttributeOverrides', '@AttributeOverride', '@AssociationOverrides',
                      '@AssociationOverride', '@AssociationOverride', '@AttributeAccessor', '@AttributeAccessor'}


@dataclass
class AnnotationInfo:
    name: str
    line_number: int
    parameters: Dict[str, str] = field(default_factory=dict)


class ObjectType(Enum):
    STRING = "String"
    STRING_BUILDER = "StringBuilder"

    @staticmethod
    def type_of_interest(value):
        return any(value == item.value for item in ObjectType)


class ExpressionType(Enum):
    METHOD_CALL = "method_call"
    OBJECT_CREATION = "object_creation"


@dataclass
class ExpressionInfo:
    name: str | None
    content: str
    line_number: int
    type: ObjectType
    expression_type: ExpressionType | None
    method_calls: List['ExpressionInfo'] = field(default_factory=list)

    def __str__(self):
        ret = ''
        if self.expression_type == ExpressionType.OBJECT_CREATION:
            ret += f"Object creation: {self.name} type: {self.type.value} content: {self.content}\n"
            for call in self.method_calls:
                ret += str(call)
        if self.expression_type == ExpressionType.METHOD_CALL:
            return f"Method call: {self.name} type: {self.type.value} content: {self.content}\n"
        return ret



@dataclass
class Scope:
    expressions: List[Dict[str, ExpressionInfo]] = field(default_factory=list)
    parent: Optional['Scope'] = field(default=None)
    children: List['Scope'] = field(default_factory=list)

    def __str__(self):
        r = ''
        for child in self.children:
            r += child.__str__()
            return r
        else:
            for expression_dict in self.expressions:
                for expression_name, expression_info in expression_dict.items():
                    r += f"{expression_name}: {expression_info}\n"
            return r

    def get_object_scope(self, object_name: str) -> Union['Scope', None]:
        for expression_dict in self.expressions:
            if object_name in expression_dict:
                return self
        if self.parent:
            return self.parent.get_object_scope(object_name)
        return None

    def is_empty(self):
        if self.expressions:
            return False
        for child in self.children:
            if not child.is_empty():
                return False
        return True

    def get_expression_by_name(self, expression_name: str) -> Union[ExpressionInfo, None]:
        for expression_dict in self.expressions:
            if expression_name in expression_dict:
                return expression_dict[expression_name]
        return None


@dataclass
class MethodInfo:
    name: str
    line_number: int
    return_type: str
    annotations: List[AnnotationInfo] = field(default_factory=list)
    scope: Scope = field(default_factory=Scope)


@dataclass
class FieldInfo:
    name: str
    line_number: int
    type: str
    value: str | None = None
    annotations: List[AnnotationInfo] = field(default_factory=list)


class ReferenceType(Enum):
    CLASS = "class"
    INTERFACE = "interface"
    RECORD = "record"
    ANNOTATION = "annotation"
    ENUM = "enum"


@dataclass
class InheritanceInfo:
    name: str = None
    generic_parameters: List[str] = field(default_factory=list)


@dataclass
class ReferenceTypeInfo:
    name: str
    line_number: int
    type: ReferenceType
    annotations: List[AnnotationInfo] = field(default_factory=list)
    extends: List[InheritanceInfo] = None
    implements: List[InheritanceInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)


@dataclass
class JavaFileInfo:
    file_name: str | None
    file_path: str | None
    package_name: str
    imports: List[str] = field(default_factory=list)
    reference_types: List[ReferenceTypeInfo] = field(default_factory=list)

    def print_human_readable(self):
        print(f"Package: {self.package_name}")
        print(f"Imports: {', '.join(self.imports)}")
        for cls in self.reference_types:
            print(f"Class: {cls.name}")

            for annotation in cls.annotations:
                # Initialize the string to store the annotation details
                annotation_details = f"Annotation: {annotation.name if annotation.name else 'None'}"

                # Append parameters to the annotation details if they exist
                if annotation.parameters:
                    params_string = ', '.join(f"{param}: {val}" for param, val in annotation.parameters.items())
                    annotation_details += f" with parameters: [{params_string}]"
                else:
                    annotation_details += " with no parameters"

                # Print the compiled annotation details
                print(annotation_details)

            if cls.extends:
                print(f"  Extends: {cls.extends}")
            if cls.implements:
                print(f"  Implements: {', '.join(cls.implements)}")
            print("  Fields:")
            for field in cls.fields:
                print(f"    {field.name},  Type: {field.type}, Value: {field.value}")
                for annotation in field.annotations:
                    print(f"      Annotation: {annotation.name}")
                    if annotation.parameters:
                        print(f"      Parameters: {annotation.parameters}")
            print("  Methods:")
            for method in cls.methods:
                print(f"    {method.name},  Return Type: {method.return_type}")
                for annotation in method.annotations:
                    print(f"      Annotation: {annotation.name}")
                    if annotation.parameters:
                        print(f"      Parameters: {annotation.parameters}")
                print("      Scope:")
                print(method.scope)
