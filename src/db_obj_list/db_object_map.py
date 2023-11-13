import re
import csv
from pathlib import Path
from dataclasses import dataclass
from metadata import *
from db_object_read import *
from typing import Set, List, Iterator

OBJECT_TYPES = {'TABLE', 'VIEW', 'PROCEDURE', 'PACKAGE', 'TRIGGER', 'FUNCTION', 'MATERIALIZED_VIEW'}
# OWNERS = {'A_RAIABD'}

OWNERS = {'A_RAIABD', 'NFE', 'SISBF', 'MSAF_DFE',
          'USR_ITIMPRO', 'USR_MS_ESTOQ', 'USR_MS_DESCON', 'USR_MAG', 'USR_MS_PAGTO',
          'USR_MS_PEDIDO', 'USR_MS_PEDSYNC', 'USR_MS_REMARCACAO', 'USR_MS_FARMPOPULAR',
          'USR_MS_PRECO', 'USR_MS_ASSINA', 'USR_MS_JOR_CONS', 'USRSICOFI', 'USR_QLIKVIEW', 'PRODUCAO', 'USR_MONITORRD',
          'USR_MS_WALLET', 'USR_MS_PEDIDO_PRD', 'USR_LGPD', 'USR_MS_ESTOQ_PRD', 'USR_MS_REMARCACAO_PRD', 'CONSULTA',
          'USR_MS_UNFIT_SYNC', 'USR_MS_PAGTO_PRD', 'USR_MS_DESCON_PRD', 'US_EXCRM', 'USR_MS_PEDSYNC_PRD',
          'USR_MS_ENTREGA', 'USR_MTZ', 'USR_MS_FARMPOPULAR_PRD', 'USR_MS_ASSINA_PRD', 'USR_MS_PRECO_PRD',
          'USR_MS_MKTP_FINANCEIRO', 'USR_MS_FUNCIONARIO', 'REMOTE_SCHEDULER_AGENT', 'USR_MS_MKTP_VENDEDOR',
          'USR_WORKFLOW', 'OUTLN', 'USR_MS_ENTREGA_PRD', 'USR_PRODMTZ', 'USR_MS_WALLET_PRD', 'DBSFWUSER', 'ORACLE_OCM',
          'USR_MS_UNFIT_CONS', 'USR_MS_OFERTA_SYNC', 'AS_TC', 'USR_MS_MEDICO', 'USR_MS_FIDELIDADE_SYNC',
          'CTMSERVICE', 'USR_MS_MKTP_INTEGRA', 'USR_MS_MKTP_VENDEDOR_PRD', 'USR_MS_FUNCIONARIO_PRD',
          'USR_MS_MKTP_FINANCEIRO_PRD', 'USR_ZABBIX_V8', 'USR_MS_MKTP_INTEGRA_PRD', 'AVUSER',
          'USR_MS_MEDICO_PRD', 'USROFERTAS', 'USR_MS_MKTP_CATALOGO', 'USR_MS_MKTP_PEDIDO', 'USR_DELPHIX',
          'USR_MS_MKTP_CATALOGO_PRD', 'USR_SOLIC', 'USR_MS_MKTP_PEDIDO_PRD', 'USR_DELPHIX2'}


@dataclass
class TokenInfo:
    owner: str
    object_name: str
    object_type: str
    line: str
    line_number: int
    file_path: str
    file_name: str
    repo_name: str


dq_string_pattern = re.compile(r'"(.*?)"')  # double quotes strings
sq_string_pattern = re.compile(r"'(.*?)'")  # single quotes strings
js_string_pattern = re.compile(r"('(?:\\.|[^\\'])*')|(\"(?:\\.|[^\\\"])*\")|(`(?:\\.|[^\\`])*`)")
php_string_pattern = re.compile(r"('(?:\\.|[^\\'])*')|(\"(?:\\.|[^\\\"])*\")|(<<<[^\s]+[\s\S]*?^\2;?$)")
token_pattern = re.compile(r'[,;:\s]\s*')


def find_java_strings(text: str) -> List[str]:
    return re.findall(dq_string_pattern, text)


def find_sql_strings(text: str) -> List[str]:
    return re.findall(dq_string_pattern, text)


def find_php_strings(text: str) -> List[str]:
    matches = php_string_pattern.findall(text)
    return [string for group in matches for string in group if string]


def find_js_strings(text: str) -> List[str]:
    matches = js_string_pattern.findall(text)
    return [string for group in matches for string in group if string]


def read_file_with_fallback_encoding(file_path: Path, first_encoding='utf-8', fallback_encoding='windows-1252') -> str:
    try:
        return file_path.read_text(encoding=first_encoding)
    except UnicodeDecodeError:
        return file_path.read_text(encoding=fallback_encoding)


def process_line(line: str, line_number: int, db_object_dict: Dict[str, Dict[str, Dict[str, CodeObject]]],
                 file_info: dict, find_function) -> \
        List[TokenInfo]:
    results = []
    stripped_line = line.strip()

    for owner, type_name in db_object_dict.items():
        if owner.upper() not in OWNERS:
            continue
        for db_type, name_obj in type_name.items():
            if db_type.upper() not in OBJECT_TYPES:
                continue
            for matches in find_function(stripped_line):
                for token in re.split(token_pattern, matches):
                    object_name = name_obj.get(token.upper(), None)
                    if object_name:
                        results.append(TokenInfo(
                            owner=owner,
                            object_name=object_name.name,
                            object_type=db_type,
                            line=stripped_line,
                            line_number=line_number,
                            file_path=file_info['file_path'],
                            file_name=file_info['file_name'],
                            repo_name=file_info['repo_name']))
    return results


def find_tokens(root_directory: Path, db_object_dict: Dict[str, Dict[str, Dict[str, CodeObject]]]) -> List[TokenInfo]:
    results = []
    for file_path in root_directory.glob('**/*'):
        file_info = {
            'file_path': str(file_path.parent),
            'file_name': file_path.name,
            'repo_name': root_directory.name
        }
        match file_path.suffix.lower():
            case '.java':
                find_function = find_java_strings
            case '.sql':
                find_function = find_sql_strings
            case '.php':
                find_function = find_php_strings
            case '.js':
                find_function = find_js_strings
            case _:
                continue
        file_content = read_file_with_fallback_encoding(file_path)
        for line_number, line in enumerate(file_content.split('\n'), 1):
            results.extend(process_line(line, line_number, db_object_dict, file_info, find_function))
    return results


def write_csv_from_token_info(token_info_list: List[TokenInfo], file_path: str):
    field_names = ['Owner', 'Object Name', 'Object Type', 'Line', 'Line Number', 'File Path', 'File Name', 'Repo Name',
                   'Valid', 'Operation']

    with open(file_path, 'w', newline='', errors='replace') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        for token_info in token_info_list:
            # try:
            writer.writerow({
                'Owner': token_info.owner,
                'Object Name': token_info.object_name,
                'Object Type': token_info.object_type,
                'Line': token_info.line,
                'Line Number': token_info.line_number,
                'File Path': token_info.file_path,
                'File Name': token_info.file_name,
                'Repo Name': token_info.repo_name,
                'Valid': '',
                'Operation': ''
            })
        # except UnicodeEncodeError:
        #     print(token_info)


if __name__ == '__main__':
    csv_filepath = "../../examples/r102_objects.csv"
    origin = Origin(name="R102", description="R102 oracle database instance", type=OriginType.ORACLE_DB)
    objects = get_oracle_objects_from_csv(origin=origin,
                                          csv_filepath=csv_filepath)

    # generate indexes for the db objects
    db_object_dict = {}
    for db_object in objects:
        # Initialize the namespace dictionary if it doesn't exist
        if db_object.namespace not in db_object_dict:
            db_object_dict[db_object.namespace] = {}

        # Initialize the type dictionary if it doesn't exist
        if db_object.type.value not in db_object_dict[db_object.namespace]:
            db_object_dict[db_object.namespace][db_object.type.value] = {}

        # Now you can safely assign the db_object to the innermost dictionary
        db_object_dict[db_object.namespace][db_object.type.value][db_object.name] = db_object

    # root_directory = Path("../../examples/PortalTC-Core-master")
    # root_directory = Path("../../examples/OMS")
    # root_directory = Path("../../examples/ofex-master")
    root_directory = Path("../../examples/rd-estoque-master")
    # root_directory = Path("../../examples/Emissor NFE")
    result = []

    result.extend(find_tokens(root_directory, db_object_dict))

    output_file_name = root_directory.name + '.csv'

    write_csv_from_token_info(result, Path('../../output/' + output_file_name))
