from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Tuple, NamedTuple, List, Set
from tree_sitter import Language, Tree


class OriginType(Enum):
    JAVA = 'java'
    PHP = 'php'
    JAVASCRIPT = 'javascript'
    ORACLE_DB = 'oracle_db'


class RelationshipType(Enum):
    READ = 'read'
    MODIFY = 'modify'
    CALL = 'call'
    ENTITY_DEF = 'entity_def'
    REPOSITORY_DEF = 'repository_def'
    REPOSITORY_METHOD_DEF = 'repository_method_def'
    REPOSITORY_METHOD_INVOCATION = 'repository_method_invocation'


class ObjectType(Enum):
    pass


class JavaCodeObjectType(ObjectType):
    ENTITY_CLASS = 'ENTITY_CLASS'
    REPOSITORY_INTERFACE = 'REPOSITORY_INTERFACE'
    REPOSITORY_METHOD = 'REPOSITORY_METHOD'
    VARIABLE = 'VARIABLE'


class OracleCodeObjectType(ObjectType):
    TABLE = 'TABLE'
    VIEW = 'VIEW'
    MATERIALIZED_VIEW = 'MATERIALIZED VIEW'
    PROCEDURE = 'PROCEDURE'
    FUNCTION = 'FUNCTION'
    TRIGGER = 'TRIGGER'
    SEQUENCE = 'SEQUENCE'
    SYNONYM = 'SYNONYM'
    TYPE = 'TYPE'
    TYPE_BODY = 'TYPE BODY'
    PACKAGE = 'PACKAGE'
    PACKAGE_BODY = 'PACKAGE BODY'
    INDEX = 'INDEX'
    CONSTRAINT = 'CONSTRAINT'
    GRANT = 'GRANT'
    JOB = 'JOB'

    @classmethod
    def from_string(cls, value_string: str):
        return next((item for item in cls if item.value == value_string), None)


@dataclass(frozen=True)
class Origin:
    type: OriginType
    name: str
    description: str
    file_path_root: str | None = None

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Origin):
            return False
        return self.name == other.name and self.type == other.type


@dataclass(frozen=True)
class SourceFile:
    origin: Origin
    file_name: str
    file_path: str
    content: str | None = None
    language: Language | None = None
    tree: Tree | None = None

    def __hash__(self):
        return hash((self.origin, self.file_name, self.file_path))

    def __eq__(self, other):
        if not isinstance(other, SourceFile):
            return False
        return (
                self.origin == other.origin and
                self.file_name == other.file_name and
                self.file_path == other.file_path
        )


@dataclass(frozen=True)
class CodeObject:
    source_file: SourceFile
    namespace: str
    name: str
    type: ObjectType
    position: Tuple[int, int] | None = None

    def __hash__(self):
        return hash((self.type, self.source_file, self.namespace, self.name))

    def __eq__(self, other):
        if not isinstance(other, CodeObject):
            return False
        return (self.type == other.type and self.source_file == other.source_file and
                self.namespace == other.namespace and self.name == other.name)


class ObjectIndexKey(NamedTuple):
    origin: Origin
    namespace: str
    type: ObjectType


class ObjectTypeIndex:
    def __init__(self) -> None:
        self.index: Dict[ObjectIndexKey, Set[CodeObject]] = {}

    def add_item(self, keys: ObjectIndexKey, item: CodeObject) -> None:
        if keys not in self.index:
            self.index[keys] = set()
        self.index[keys].add(item)

    def get_item(self, keys: ObjectIndexKey) -> Set[CodeObject]:
        if keys not in self.index:
            return set()

        return self.index[keys]


    def remove_item(self, keys: ObjectIndexKey) -> None:
        try:
            del self.index[keys]
        except KeyError:
            raise KeyError(f"No item found for keys: {keys}")


@dataclass
class ObjectMapping:
    relationship: RelationshipType
    from_object: CodeObject
    to_object: CodeObject
