import os
import re
import csv
from dataclasses import dataclass, field
from typing import List, Set

@dataclass(frozen=True)  # The `frozen=True` argument makes the dataclass immutable, hence hashable.
class DatabaseObject:
    owner: str
    object_name: str
    object_type: str

    def __hash__(self):
        return hash((self.owner, self.object_name, self.object_type))

@dataclass
class Occurrence:
    file_path: str
    package_name: str
    class_name: str
    lines: List[int]

@dataclass
class JavaFile:
    file_path: str
    package_name: str
    class_name: str
    content: str

@dataclass
class TableUsage:
    table_name: str
    read: bool = False
    modified: bool = False
    occurrences: List[Occurrence] = field(default_factory=list)

class TableUsageTracker:
    def __init__(self):
        self.table_usages = []

    def add_usage(self, table_usage: TableUsage):
        for existing_usage in self.table_usages:
            if existing_usage.table_name == table_usage.table_name:
                existing_usage.read |= table_usage.read
                existing_usage.modified |= table_usage.modified
                existing_usage.occurrences.extend(table_usage.occurrences)
                break
        else:
            self.table_usages.append(table_usage)

    def print_usage(self):
        for table_usage in sorted(self.table_usages, key=lambda x: x.table_name):
            actions = []
            if table_usage.read:
                actions.append('read')
            if table_usage.modified:
                actions.append('modified')
            print(f'{table_usage.table_name}: {", ".join(actions)}')
            for occurrence in table_usage.occurrences:
                print(
                    f'  - File: {occurrence.file_path}, Package: {occurrence.package_name}, Class: '
                    f'{occurrence.class_name}, Lines: {", ".join(map(str, occurrence.lines))}'
                )

def identify_tables(java_file: JavaFile) -> TableUsageTracker:
    read_patterns = [
        re.compile(r'SELECT\s.*?\sFROM\s+(\w+)', re.IGNORECASE | re.DOTALL),
        re.compile(r'JOIN\s+(\w+)\s', re.IGNORECASE | re.DOTALL)
    ]
    modify_patterns = [
        re.compile(r'(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)', re.IGNORECASE)
    ]

    tracker = TableUsageTracker()
    for line_num, line in enumerate(java_file.content.split('\n'), start=1):
        for pattern in read_patterns:
            for match in pattern.finditer(line):
                table_name = match.group(1).upper()
                occurrence = Occurrence(
                    file_path=java_file.file_path,
                    package_name=java_file.package_name,
                    class_name=java_file.class_name,
                    lines=[line_num]
                )
                table_usage = TableUsage(table_name=table_name, read=True, occurrences=[occurrence])
                tracker.add_usage(table_usage)
        for pattern in modify_patterns:
            for match in pattern.finditer(line):
                table_name = match.group(2).upper()
                occurrence = Occurrence(
                    file_path=java_file.file_path,
                    package_name=java_file.package_name,
                    class_name=java_file.class_name,
                    lines=[line_num]
                )
                table_usage = TableUsage(table_name=table_name, modified=True, occurrences=[occurrence])
                tracker.add_usage(table_usage)

    return tracker

def extract_package_class(file_path: str) -> JavaFile:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    package_match = re.search(r'package\s+([\w.]+);', content)
    class_match = re.search(r'class\s+(\w+)', content)
    package_name = package_match.group(1) if package_match else None
    class_name = class_match.group(1) if class_match else None
    return JavaFile(file_path=file_path, package_name=package_name, class_name=class_name, content=content)

def read_csv(csv_filepath: str, owner_filter=None) -> Set[DatabaseObject]:
    db_objects = set()
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            if owner_filter and row['OWNER'].upper() != owner_filter.upper():
                continue
            if row['OBJECT_TYPE'].upper() in {'TABLE', 'VIEW', 'MATERIALIZED VIEW'}:
                db_object = DatabaseObject(owner=row['OWNER'], object_name=row['OBJECT_NAME'], object_type=row['OBJECT_TYPE'])
                db_objects.add(db_object)
    return db_objects

def main(csv_filepath: str, root_dir: str, owner_filter=None):
    db_objects = read_csv(csv_filepath, owner_filter)
    db_object_names = {db_object.object_name for db_object in db_objects}
    master_tracker = TableUsageTracker()
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                java_file = extract_package_class(file_path)
                table_usage_tracker = identify_tables(java_file)
                for table_usage in table_usage_tracker.table_usages:
                    if table_usage.table_name in db_object_names:
                        master_tracker.add_usage(table_usage)

    master_tracker.print_usage()

if __name__ == "__main__":
    csv_filepath = "../../examples/r102_objects.csv"
    owner_filter = 'A_RAIABD'  # replace with the desired owner name
    root_dir = '../../examples/PortalTC-Core-master/src'  # replace with the root directory of your Java application source code
    main(csv_filepath, root_dir, owner_filter)
