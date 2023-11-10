import csv
import os
from metadata import *
from typing import Set


def get_oracle_objects_from_csv(origin: Origin, csv_filepath: str) -> Set[CodeObject]:
    source_file = SourceFile(origin=origin, file_name=os.path.basename(csv_filepath),
                             file_path=os.path.dirname(csv_filepath))

    objects: Set[CodeObject] = set()
    db_object_types = {item.value: item for item in OracleCodeObjectType}

    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            if row['OBJECT_TYPE'].upper() not in db_object_types.keys():
                continue

            objects.add(CodeObject(source_file=source_file,
                                   namespace=row['OWNER'].upper(),
                                   name=row['OBJECT_NAME'].upper(),
                                   type=db_object_types[row['OBJECT_TYPE'].upper()]))

    return objects


def generate_index(code_objects: Set[CodeObject]) -> ObjectTypeIndex:
    index = ObjectTypeIndex()
    for code_object in code_objects:
        index.add_item(ObjectIndexKey(origin=code_object.source_file.origin,
                                      namespace=code_object.namespace,
                                      type=code_object.type),
                       code_object)
    return index


if __name__ == '__main__':
    csv_filepath = "../../examples/r102_objects.csv"
    origin = Origin(name="R102", description="R102 oracle database instance", type=OriginType.ORACLE_DB)
    objects = get_oracle_objects_from_csv(origin=origin,
                                          csv_filepath=csv_filepath)

    idx = generate_index(objects)

    item_key = ObjectIndexKey(origin=origin,
                              namespace="A_RAIABD",
                              type=OracleCodeObjectType.TABLE)

    print(f'Looking up key: {item_key}')

    print(idx.get_item(item_key))
