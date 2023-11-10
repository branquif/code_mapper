import csv
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple, NamedTuple
from tree_sitter import Language, Parser, Tree


class OriginType(Enum):
    JAVA = 'java'
    PHP = 'php'
    JAVASCRIPT = 'javascript'
    ORACLE_DB = 'oracle_db'


@dataclass(frozen=True)
class Origin:
    name: str
    description: str
    type: OriginType
    file_path_root: str | None = None

    def __hash__(self):
        return hash((self.name, self.type))


@dataclass
class SourceFile:
    origin: Origin
    file_name: str | None = None
    file_path: str | None = None
    content: str | None = None
    language: Language | None = None
    tree: Tree | None = None


class CodeObjectType(Enum):
    pass


class JavaCodeObjectType(CodeObjectType):
    ENTITY_CLASS = 'entity_class'
    REPOSITORY_INTERFACE = 'repository_interface'
    REPOSITORY_METHOD = 'repository_method'
    VARIABLE = 'variable'


class OracleCodeObjectType(CodeObjectType):
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


@dataclass
class CodeObject:
    source_file: SourceFile
    namespace: str
    name: str
    type: CodeObjectType
    position: Tuple[int, int]


class ObjectIndexKey(NamedTuple):
    origin: Origin
    namespace: str
    name: str


class CodeObjectTypeIndex:
    """find code objects byt the ObjectIndexKey, which is a combination of origin, namespace and name"""
    def __init__(self) -> None:
        self.index: Dict[ObjectIndexKey, CodeObject] = {}

    def add_item(self, keys: ObjectIndexKey, item: CodeObject) -> None:
        self.index[keys] = item

    def get_item(self, keys: ObjectIndexKey) -> CodeObject:
        try:
            return self.index[keys]
        except KeyError:
            raise KeyError(f"No item found for keys: {keys}")

    def remove_item(self, keys: ObjectIndexKey) -> None:
        try:
            del self.index[keys]
        except KeyError:
            raise KeyError(f"No item found for keys: {keys}")


class RelationType(Enum):
    DB_OBJ_READ = 'read'
    DB_OBJ_MODIFY = 'modify'
    PROCEDURE_CALL = 'call'
    ENTITY_DEF = 'entity_def'
    REPO_CLASS_DEF = 'repository_def'
    REPO_METHOD_DEF = 'repository_method_def'
    REPO_METHOD_INVOCATION = 'repository_method_invocation'


@dataclass
class ObjectMapping:
    from_object: CodeObject
    to_object: CodeObject
    relationship: RelationType


READ_PATTERNS = [
    re.compile(r'SELECT\s.*?\sFROM\s+(\w+)', re.IGNORECASE | re.DOTALL),
    re.compile(r'JOIN\s+(\w+)\s', re.IGNORECASE | re.DOTALL)
]
MODIFY_PATTERNS = [
    re.compile(r'(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)', re.IGNORECASE)
]


class DBObjectUsageTracker:
    def __init__(self):
        self.object_usages = []

    def add_usage(self, object_usage: DBObjectMapping):
        for existing_usage in self.object_usages:
            if existing_usage.table_name == object_usage.object_name:
                existing_usage.read |= object_usage.read
                existing_usage.modified |= object_usage.modified
                existing_usage.occurrences.extend(object_usage.occurrences)
                break
        else:
            self.object_usages.append(object_usage)

    def print_usage(self):
        for object_usage in sorted(self.object_usages, key=lambda x: x.table_name):
            actions = []
            if object_usage.read:
                actions.append('read')
            if object_usage.modified:
                actions.append('modified')
            print(f'{object_usage.table_name}: {", ".join(actions)}')
            for occurrence in object_usage.occurrences:
                print(
                    f'  - File: {occurrence.file_path}, Package: {occurrence.package_name}, Class: '
                    f'{occurrence.class_name}, Lines: {", ".join(map(str, occurrence.lines))}'
                )


def get_db_objects_from_csv(csv_filepath: str) -> dict[str, Set[DatabaseObjects]]:
    db_objects: Dict[str, DatabaseObjects] = {}
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            owner = row['OWNER'].upper()
            db_object = DatabaseObject(owner=owner,
                                       object_name=row['OBJECT_NAME'].upper(),
                                       object_type=row['OBJECT_TYPE'].upper())

            if owner not in db_objects:
                db_objects[owner] = DatabaseObjects(owner=owner)

            db_objects[owner].all.add(db_object)
            match row['OBJECT_TYPE'].upper():
                case 'TABLE':
                    db_objects[owner].tables[db_object.object_name] = db_object
                case 'VIEW':
                    db_objects[owner].views[db_object.object_name] = db_object
                case 'PACKAGE':
                    db_objects[owner].packages[db_object.object_name] = db_object
                case 'PROCEDURE':
                    db_objects[owner].procedures[db_object.object_name] = db_object
                case 'FUNCTION':
                    db_objects[owner].functions[db_object.object_name] = db_object
                case 'TRIGGER':
                    db_objects[owner].triggers[db_object.object_name] = db_object
                case 'SEQUENCE':
                    db_objects[owner].sequences[db_object.object_name] = db_object
                case 'SYNONYM':
                    db_objects[owner].synonyms[db_object.object_name] = db_object
                case 'TYPE':
                    db_objects[owner].types[db_object.object_name] = db_object
                case 'MATERIALIZED VIEW':
                    db_objects[owner].materialized_views[db_object.object_name] = db_object
                case 'INDEX':
                    db_objects[owner].indexes[db_object.object_name] = db_object
                case 'CONSTRAINT':
                    db_objects[owner].constraints[db_object.object_name] = db_object
                case 'GRANT':
                    db_objects[owner].grants[db_object.object_name] = db_object

    return db_objects


def identify_db_objects_in_string_var(identifier: Identifier, variable_str: str, db_owner: str,
                                      db_objects: Dict[str, DatabaseObjects]) -> List[DBObjectMapping]:
    """
    Identify the database objects in the variable string. This function is not perfect and will return a lot of false
    positives. A pass through the actual list of db objects will be needed to filter out the false positives.
    :param identifier: the identifier that contains the variable string to be analyzed
    :param variable_str: the variable string to be analyzed
    :param db_owner: the owner of the database objects for reference
    :param db_objects: the database objects
    :return: list of DBObjectUsage that can be identified within the variable string
    """

    def get_db_object_and_type(db_object_name: str, db_owner: str, db_objects: Dict[str, DatabaseObjects]) -> Tuple[
        Any, str]:
        for object_type, dict_name in [('TABLE', 'tables'), ('VIEW', 'views'),
                                       ('MATERIALIZED VIEW', 'materialized_views')]:
            db_object_dict = getattr(db_objects[db_owner], dict_name)
            if db_object_name in db_object_dict:
                return db_object_dict[db_object_name], object_type
        return None, None

    db_object_usages = []

    for pattern in READ_PATTERNS:
        for match in pattern.finditer(variable_str):
            db_object_name = match.group(1).upper()
            db_object, object_type = get_db_object_and_type(db_object_name, db_owner, db_objects)
            if object_type:
                db_object_usages.append(
                    DBObjectMapping(identifier=identifier, db_object=db_object, operation=DBOperation.READ))

    for pattern in MODIFY_PATTERNS:
        for match in pattern.finditer(variable_str):
            db_object_name = match.group(2).upper()
            db_object, object_type = get_db_object_and_type(db_object_name, db_owner, db_objects)
            if object_type:
                db_object_usages.append(
                    DBObjectMapping(identifier=identifier, db_object=db_object, operation=DBOperation.MODIFY))

    return db_object_usages
