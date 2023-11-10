import os
import re
import csv
from dataclasses import dataclass, field
from typing import List, Set
from tree_sitter import Language, Parser, Tree


def build_languages():
    Language.build_library(
        '../../vendor/build/my-languages.so',
        [
            '../../vendor/tree-sitter/tree-sitter-java',
            '../../vendor/tree-sitter/tree-sitter-javascript',
            '../../vendor/tree-sitter/tree-sitter-php'
        ]
    )
    JV_LANGUAGE = Language('../../vendor/build/my-languages.so', 'java')
    return JV_LANGUAGE


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
    tree:
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




def process_java_file(file_path: str) -> JavaFile:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    package_match = re.search(r'package\s+([\w.]+);', content)
    class_match = re.search(r'class\s+(\w+)', content)
    package_name = package_match.group(1) if package_match else None
    class_name = class_match.group(1) if class_match else None
    return JavaFile(file_path=file_path, package_name=package_name, class_name=class_name, content=content)






def main(java_filepath):
    language = build_languages()
    tree, code = parse_java_file(java_filepath, language)
    strings_list = find_string_variables(language, tree)
    for position, concatenated_string in strings_list:
        print(f'{position} - {concatenated_string}')


if __name__ == "__main__":
    java_filepath = '../../examples/PortalTC-Core-master/src/br/com/drogaraia/tc/vo/QueriesConsultasProduto.java'
    main(java_filepath)
