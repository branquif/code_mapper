import csv
import re
from collections import defaultdict


def load_db_objects(csv_filepath, owner_filter=None):
    db_objects = set()
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            if owner_filter and row['OWNER'].upper() != owner_filter.upper():
                continue
            if row['OBJECT_TYPE'].lower() in {'table', 'view', 'materialized view'}:
                db_objects.add(row['OBJECT_NAME'].upper())
    return db_objects


def identify_tables(java_code):
    table_pattern = re.compile(r'\b([A-Z_][A-Z0-9_]*)\b')
    tables_in_code = defaultdict(set)
    for line_no, line in enumerate(java_code.split('\n'), 1):
        for table_name in re.findall(table_pattern, line):
            tables_in_code[table_name].add(line_no)
    return tables_in_code


def categorize_table_usage(java_code, table_name):
    read_pattern = re.compile(fr'(?i)SELECT.*?FROM.*?\b{table_name}\b', re.DOTALL)
    modify_pattern = re.compile(fr'(?i)(INSERT INTO|UPDATE|DELETE FROM)\b.*?\b{table_name}\b', re.DOTALL)
    is_read = bool(read_pattern.search(java_code))
    is_modified = bool(modify_pattern.search(java_code))
    return is_read, is_modified


def main(csv_filepath, java_filepath, owner_filter=None):
    db_objects = load_db_objects(csv_filepath, owner_filter)

    with open(java_filepath, 'r', encoding='utf-8') as file:
        java_code = file.read()

    tables_in_code = identify_tables(java_code)

    table_usage = defaultdict(lambda: {'read': False, 'modified': False, 'lines': set()})
    for table_name, lines in tables_in_code.items():
        if table_name in db_objects:
            is_read, is_modified = categorize_table_usage(java_code, table_name)
            table_usage[table_name]['read'] = is_read
            table_usage[table_name]['modified'] = is_modified
            table_usage[table_name]['lines'].update(lines)

    # Sort table_usage by table name
    sorted_table_usage = dict(sorted(table_usage.items()))

    for table_name, usage in sorted_table_usage.items():
        actions = []
        if usage['read']:
            actions.append('read')
        if usage['modified']:
            actions.append('modified')
        lines = ', '.join(map(str, sorted(usage['lines'])))
        print(f'{table_name}: {", ".join(actions)}; Lines: {lines}')


if __name__ == "__main__":
    # Define the file paths
    # Provide the file name where the Java code is saved
    java_filepath = '../../examples/PortalTC-Core-master/src/br/com/drogaraia/tc/vo/QueriesConsultasProduto.java'
    csv_filepath = "../../examples/r102_objects.csv"
    owner_filter = 'A_RAIABD'  # replace with the desired owner name

    main(csv_filepath, java_filepath, owner_filter)
