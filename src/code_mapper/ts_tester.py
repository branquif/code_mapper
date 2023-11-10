from tree_sitter import Language, Parser
from pathlib import Path

Language.build_library(
    # Store the library in the `build` directory
    str(Path('../../vendor/build/my-languages.so')),
    # '../../vendor/build/my-languages.so',

    # Include one or more languages
    [
        str(Path('../../vendor/tree-sitter/tree-sitter-java')),
        str(Path('../../vendor/tree-sitter/tree-sitter-javascript')),
        str(Path('../../vendor/tree-sitter/tree-sitter-php'))
    ]
)

JV_LANGUAGE = Language(str(Path('../../vendor/build/my-languages.so')), 'java')
JS_LANGUAGE = Language(str(Path('../../vendor/build/my-languages.so')), 'javascript')
PH_LANGUAGE = Language(str(Path('../../vendor/build/my-languages.so')), 'php')

parser = Parser()
parser.set_language(JV_LANGUAGE)

jv_example_file = str(Path(
    '../../examples/rd-estoque-master/estoque-model-impl/src/main/java/com/raiadrogasil/api/repository/type/ProdutoEstoqueEntity.java'))

with open(jv_example_file) as file:
    code = file.read()

tree = parser.parse(bytes(code, "utf8"))

query_entity = """
(program (package_declaration (scoped_identifier) @pkg))

(class_declaration
    (modifiers
        (marker_annotation name: (identifier) @single_annotation
        	(#eq? @single_annotation "Entity"))
        (annotation
          name: (identifier) @annotation-name (#eq? @annotation-name "Table")
          arguments: (annotation_argument_list
            (element_value_pair
              key: (identifier) @key (#eq? @key "name")
              value: (string_literal) @table_name
            )
          )
        )*
    )
    name: (identifier) @class_name
    body: (class_body) @cls_body
)
"""

query = JV_LANGUAGE.query(query_entity)
captures = query.captures(tree.root_node)

# get full qualified class name
for c in captures:
    # print(f"{c[1]}: {c[0].text}")
    if c[1] == 'pkg':
        package = c[0].text.decode('utf8').replace('"', '')
    if c[1] == 'class_name':
        class_name = c[0].text.decode('utf8').replace('"', '')
    if c[1] == 'table_name':
        table_name = c[0].text.decode('utf8').replace('"', '')
    if c[1] == 'cls_body':
        cls_body = c[0].text.decode('utf8').replace('"', '')

print(f"{package}.{class_name} - {table_name}")
