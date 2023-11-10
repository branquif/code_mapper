from source_code_metadata import *
import os
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


def find_package_class(language: Language, tree: Tree) -> tuple[str, str]:
    tsq_package_class = """(package_declaration (scoped_identifier) @package)
                            (class_declaration name: (identifier) @class_name)
                        """
    query = language.query(tsq_package_class)
    captures = query.captures(tree.root_node)

    package, class_name = '', ''
    for capture in captures:
        text = capture[0].text.decode('utf8')
        type = capture[1]

        if type == "package":
            package = text
        elif type == "class_name":
            class_name = text

    return package, class_name


def parse_java_file(java_filepath: str, language: Language) -> tuple[Tree, str]:
    parser = Parser()
    parser.set_language(language)
    with open(java_filepath, 'r', encoding='utf-8') as file:
        code = file.read()
    tree = parser.parse(bytes(code, 'utf8'))
    return tree, code


def find_string_variables(language: Language, tree: Tree) -> dict[str, tuple[str, int]]:
    def extract_string(input_str: str) -> str:
        """cleans the string read from the tree-sitter node"""
        lines = input_str.split('\n')
        result = []
        in_quotes = False
        current_fragment = ''
        for line in lines:
            if '//' in line:
                line = line.split('//')[0]  # Ignore everything after //
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes  # Toggle in_quotes flag
                    if not in_quotes:
                        result.append(current_fragment)
                        current_fragment = ''
                elif in_quotes:
                    current_fragment += char
        return ''.join(result)

    tsq_str_multi_line1 = """(field_declaration
                              type: (type_identifier) @_type (#eq? @_type "String")
                              declarator: (variable_declarator
                                name: (identifier) @str_name
                                value: [
                                    (binary_expression) @str
                                    (string_literal) @str
                                    ]
                              )
                            )

    """
    query = language.query(tsq_str_multi_line1)
    captures = query.captures(tree.root_node)

    string_variables = {}
    variable_name = ''
    for capture in captures:
        text = capture[0].text.decode('utf8')
        type = capture[1]

        if type == 'str_name':
            variable_name = text
            string_variables[variable_name] = ('', 0)
            continue
        elif type == 'str':
            string_variables[variable_name] = (extract_string(text), capture[0].start_point)

    return string_variables


def string_analysis(source_file: SourceFile, package_name, class_name, db_objects: DatabaseObjects, owner: str) -> list[DBObjectUsage]:
    string_variables = find_string_variables(source_file.language, source_file.tree)
    db_object_usages = []
    for identifier_name, val in string_variables.items():
        string_var = val[0]
        position = val[1]
        identifier = Identifier(source_file=source_file,
                                package_name=package_name,
                                class_name=class_name,
                                identifier_name=identifier_name,
                                identifier_type=IdentifierType.VARIABLE,
                                position=position
                                )


        db_object_usages.extend(identify_db_objects_in_string_var(identifier, string_var, owner, db_objects))

    return db_object_usages



def main(csv_filepath: str, root_dir: str, owner=None, analysis_type="string"):
    db_objects = get_db_objects_from_csv(csv_filepath)
    language = build_languages()
#    master_tracker = DBObjectUsageTracker()
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                tree, code = parse_java_file(file_path, language)
                package_name, class_name = find_package_class(language, tree)
                source_file = SourceFile(language=language, file_path=file_path, tree=tree, content=code)
                if analysis_type == "string":
                    string_analysis(source_file, package_name, class_name, db_objects, owner)




if __name__ == "__main__":
    csv_filepath = "../../examples/r102_objects.csv"
    owner_filter = 'A_RAIABD'  # replace with the desired owner name
    root_dir = '../../examples/PortalTC-Core-master/src'  # replace with the root directory of your Java application
    analysis_type = "string"
    main(csv_filepath, root_dir, owner_filter, analysis_type)
