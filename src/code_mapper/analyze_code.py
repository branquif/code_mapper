import re
from metadata import *
from db_object_read import *


READ_PATTERNS = [
    re.compile(r'SELECT\s.*?\sFROM\s+(\w+)', re.IGNORECASE | re.DOTALL),
    re.compile(r'JOIN\s+(\w+)\s', re.IGNORECASE | re.DOTALL)
]
MODIFY_PATTERNS = [
    re.compile(r'(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)', re.IGNORECASE)
]


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

def process_source_code(source_origin: Origin, db_owner: str, db_idx: ObjectTypeIndex) -> Tuple[Set[CodeObject], List[ObjectMapping]]:
    if source_origin.type == OriginType.JAVA:
        return process_java_source_code(source_origin, db_owner, db_idx)


if __name__ == "__main__":
    print('hello world')