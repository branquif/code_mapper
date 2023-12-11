import re
import sys
import csv
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Set, List, Dict

OBJECT_TYPES = {'TABLE', 'VIEW', 'SYNONYM', 'PROCEDURE', 'PACKAGE', 'TRIGGER', 'FUNCTION', 'MATERIALIZED_VIEW'}
TOKEN_OF_INTEREST_READ = {'FROM', 'JOIN'} # if the token is found, it is a read
TOKEN_OF_INTEREST_MODIFY = {'INSERT', 'UPDATE', 'DELETE', 'MERGE'} # if the token is found, it is a modify

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
    valid: str = ''
    operation: str = ''


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


class CodeDbMapper:

    def __init__(self, owners: Set[str]) -> None:
        self.db_object_dict: Dict[str, Dict[str, Set[str]]] = {}
        self.owners: Set[str] = owners
        self.mapped: List[TokenInfo] = []

    def load_db_objects_csv(self, file_path: Path) -> None:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                if row['OWNER'].upper() not in self.owners:  # read only the required owners
                    continue
                if self.db_object_dict.get(row['OWNER'].upper(), None) is None:
                    # initialize the owner dictionary
                    self.db_object_dict[row['OWNER'].upper()] = {}
                if self.db_object_dict[row['OWNER'].upper()].get(row['OBJECT_TYPE'].upper(), None) is None:
                    # initialize the object type dictionary
                    self.db_object_dict[row['OWNER'].upper()][row['OBJECT_TYPE'].upper()] = set()
                self.db_object_dict[row['OWNER'].upper()][row['OBJECT_TYPE'].upper()].add(row['OBJECT_NAME'].upper())


    def find_tokens(self, root_directory: Path) -> None:
        for file_path in root_directory.glob('**/*'):
            file_info = {
                'file_path': str(file_path.parent),
                'file_name': file_path.name,
                'repo_name': root_directory.name
            }
            match file_path.suffix.lower():
                case '.java':
                    find_string_function = find_java_strings
                case '.sql':
                    find_string_function = find_sql_strings
                case '.php':
                    find_string_function = find_php_strings
                case '.js':
                    find_string_function = find_js_strings
                case _:
                    continue
            file_content = CodeDbMapper.read_file_with_fallback_encoding(file_path)
            for line_number, line in enumerate(file_content.split('\n'), 1):
                self.mapped.extend(self.process_line(line, line_number, file_info, find_string_function))

    @staticmethod
    def read_file_with_fallback_encoding(file_path: Path, first_encoding='utf-8',
                                         fallback_encoding='windows-1252') -> str:
        try:
            return file_path.read_text(encoding=first_encoding)
        except UnicodeDecodeError:
            return file_path.read_text(encoding=fallback_encoding)

    def process_line(self, line: str, line_number: int, file_info: dict, find_string_function) -> List[TokenInfo]:
        results = []
        stripped_line = line.strip()

        for owner, type_name in self.db_object_dict.items():
            if owner not in self.owners:
                continue
            for db_type, name_obj in type_name.items():
                if db_type.upper() not in OBJECT_TYPES:
                    continue
                for matches in find_string_function(stripped_line):
                    operation = ''
                    for token in re.split(token_pattern, matches):
                        if token.upper() in TOKEN_OF_INTEREST_READ:
                            operation = 'R'
                        if token.upper() in TOKEN_OF_INTEREST_MODIFY:
                            operation = 'M'
                        if token.upper() in name_obj:
                            results.append(TokenInfo(
                                owner=owner,
                                object_name=token.upper(),
                                object_type=db_type,
                                line=stripped_line,
                                line_number=line_number,
                                file_path=file_info['file_path'],
                                file_name=file_info['file_name'],
                                repo_name=file_info['repo_name'],
                                operation=operation))
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
                'Operation': token_info.operation
            })


def main(db_objects_csv: Path, owners: Set[str], root_directory: Path) -> None:
    db_code_mapper = CodeDbMapper(owners=owners)
    db_code_mapper.load_db_objects_csv(db_objects_csv)
    db_code_mapper.find_tokens(root_directory)
    output_file_name = root_directory.name + '.csv'
    write_csv_from_token_info(db_code_mapper.mapped, Path('../../output/' + output_file_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="DB Code Mapper CLI\n\nThis script requires three mandatory arguments: "
                    "a CSV file path, a root directory path, and a list of owners.",
        usage="%(prog)s csv_file root_dir owner1 [owner2 ...]",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example: %(prog)s path/to/csv/file path/to/root/dir owner1 owner2 owner3"
    )
    parser.add_argument('--db_objects_csv', type=str, help='Path to the csv file containing the database objects')
    parser.add_argument('--owners', type=str, help='Owners to be considered, separated by comma')
    parser.add_argument('--root_directory', type=str, help='Root directory to be searched for code')
    # Parse the arguments
    try:
        args = parser.parse_args()
    except argparse.ArgumentError:
        parser.print_help()
        sys.exit(1)

    root_dir_path = Path(args.root_directory)
    db_objects_csv_path = Path(args.db_objects_csv)
    owners_set = set(args.owners.split(','))
    main(db_objects_csv_path, owners_set, root_dir_path)

