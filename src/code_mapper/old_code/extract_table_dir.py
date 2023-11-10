import os
import re
import csv
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Set, List, DefaultDict


@dataclass
class TableDetails:
    lines: Set[int] = field(default_factory=set)
    read: bool = False
    modified: bool = False


@dataclass
class Occurrence:
    file_path: str
    package_name: str
    class_name: str
    lines: List[int]


def identify_tables(java_code: str) -> DefaultDict[str, TableDetails]:
    read_patterns = [
        re.compile(r'SELECT\s.*?\sFROM\s+(\w+)', re.IGNORECASE | re.DOTALL),
        re.compile(r'JOIN\s+(\w+)\s', re.IGNORECASE | re.DOTALL)
    ]
    modify_patterns = [
        re.compile(r'(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)', re.IGNORECASE)
    ]

    tables_in_code = defaultdict(TableDetails)
    for pattern in read_patterns:
        for line_num, line in enumerate(java_code.split('\n'), start=1):
            for match in pattern.finditer(line):
                table_name = match.group(1).upper()
                tables_in_code[table_name].lines.add(line_num)
                tables_in_code[table_name].read = True

    for pattern in modify_patterns:
        for line_num, line in enumerate(java_code.split('\n'), start=1):
            for match in pattern.finditer(line):
                table_name = match.group(2).upper()
                tables_in_code[table_name].lines.add(line_num)
                tables_in_code[table_name].modified = True

    return tables_in_code


def extract_package_class(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()
    package_match = re.search(r'package\s+([\w.]+);', java_code)
    class_match = re.search(r'class\s+(\w+)', java_code)
    package_name = package_match.group(1) if package_match else None
    class_name = class_match.group(1) if class_match else None
    return package_name, class_name


def process_java_file(file_path: str, db_objects: Set[str], table_usage: DefaultDict[str, List[Occurrence]]):
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()
    tables_in_code = identify_tables(java_code)
    package_name, class_name = extract_package_class(file_path)
    for table_name, details in tables_in_code.items():
        if table_name in db_objects:
            table_usage[table_name].append(
                Occurrence(
                    file_path=file_path,
                    package_name=package_name,
                    class_name=class_name,
                    lines=list(details.lines)
                )
            )


def read_csv(csv_filepath: str, owner_filter=None) -> Set[str]:
    db_objects = set()
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            if owner_filter and row['OWNER'].upper() != owner_filter.upper():
                continue
            if row['OBJECT_TYPE'].upper() in {'TABLE', 'VIEW', 'MATERIALIZED VIEW'}:
                db_objects.add(row['OBJECT_NAME'].upper())
    return db_objects


def main(csv_filepath: str, root_dir: str, owner_filter=None):
    db_objects = read_csv(csv_filepath, owner_filter)
    table_usage = defaultdict(list)
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                process_java_file(file_path, db_objects, table_usage)
    for table_name, occurrences in sorted(table_usage.items(), key=lambda x: x[0]):
        print(f'{table_name}:')
        for occurrence in occurrences:
            print(
                f'  - File: {occurrence.file_path}, Package: {occurrence.package_name}, Class: '
                f'{occurrence.class_name}, Lines: {", ".join(map(str, occurrence.lines))}'
            )


if __name__ == "__main__":
    csv_filepath = "../../examples/r102_objects.csv"
    owner_filter = 'A_RAIABD'  # replace with the desired owner name
    root_dir = '../../examples/PortalTC-Core-master/src'  # replace with the root directory of your Java application source code
    main(csv_filepath, root_dir, owner_filter)
