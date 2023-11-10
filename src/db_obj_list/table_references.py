import re
import csv
from pathlib import Path
from dataclasses import dataclass
from metadata import *
from db_object_read import *
from typing import Set, List


@dataclass
class TokenInfo:
    #owner: str
    token: str
    line: str
    line_number: int
    file_path: str
    file_name: str
    repo_name: str


def find_tokens_java(root_directory: Path, object_index: Set[CodeObject]) -> List[TokenInfo]:
    # Prepare a pattern for regex that matches any of the tokens within double quotes
    pattern = r'(?<=")[^"]*\b(?:' + '|'.join(re.escape(token.name) for token in object_index) + r')\b[^"]*(?=")'
    #pattern = r'\b(' + '|'.join(re.escape(token.name) for token in object_index) + r')\b'
    print(pattern)

    # Prepare a list to store the results
    results = []

    # Iterate over all text files in the given directory and its subdirectories
    for file_path in root_directory.glob('**/*.java'):
        # Open each file and read it line by line
        line_number = 0
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                # Use regex to find all tokens within double quotes in the line
                for match in re.findall(pattern, line):
                    # If the line contains a token from the dictionary, create a dataclass instance
                    results.append(TokenInfo(
                        token=match,
                        line=line.strip(),
                        line_number=line_number,
                        file_path=str(file_path.parent),
                        file_name=file_path.name,
                        repo_name=root_directory.name))

    return results


def write_csv_from_token_info(token_info_list: List[TokenInfo], file_path: str):
    # Define the field names for the CSV file
    field_names = ['Token', 'Line', 'Line Number', 'File Path', 'File Name', 'Repo Name', 'Read', 'Modify']

    # Open the file in write mode and create a CSV writer
    with open(file_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)

        # Write the header row
        writer.writeheader()

        # Write the data rows
        for token_info in token_info_list:
            if token_info:
                writer.writerow({
                    'Token': token_info.token,
                    'Line': token_info.line,
                    'Line Number': token_info.line_number,
                    'File Path': token_info.file_path,
                    'File Name': token_info.file_name,
                    'Repo Name': token_info.repo_name,
                    'Read': '',
                    'Modify': ''
                })


OBJECT_TYPES = {'TABLE'} #, 'VIEW', 'PROCEDURE', 'PACKAGE', 'TRIGGER', 'FUNCTION', 'MATERIALIZED_VIEW'}
OWNERS = {'A_RAIABD', 'NFE'}

# OWNERS = {'A_RAIABD', 'NFE', 'SISBF', 'MSAF_DFE',
#           'USR_ITIMPRO',  'USR_MS_ESTOQ', 'USR_MS_DESCON', 'USR_MAG', 'USR_MS_PAGTO',
#           'USR_MS_PEDIDO', 'USR_MS_PEDSYNC', 'USR_MS_REMARCACAO', 'USR_MS_FARMPOPULAR',
#           'USR_MS_PRECO', 'USR_MS_ASSINA', 'USR_MS_JOR_CONS', 'USRSICOFI', 'USR_QLIKVIEW', 'PRODUCAO', 'USR_MONITORRD',
#           'USR_MS_WALLET', 'USR_MS_PEDIDO_PRD', 'USR_LGPD', 'USR_MS_ESTOQ_PRD', 'USR_MS_REMARCACAO_PRD', 'CONSULTA',
#           'USR_MS_UNFIT_SYNC', 'USR_MS_PAGTO_PRD', 'USR_MS_DESCON_PRD', 'US_EXCRM', 'USR_MS_PEDSYNC_PRD',
#           'USR_MS_ENTREGA', 'USR_MTZ', 'USR_MS_FARMPOPULAR_PRD', 'USR_MS_ASSINA_PRD', 'USR_MS_PRECO_PRD',
#           'USR_MS_MKTP_FINANCEIRO', 'USR_MS_FUNCIONARIO', 'REMOTE_SCHEDULER_AGENT', 'USR_MS_MKTP_VENDEDOR',
#           'USR_WORKFLOW', 'OUTLN', 'USR_MS_ENTREGA_PRD', 'USR_PRODMTZ', 'USR_MS_WALLET_PRD', 'DBSFWUSER', 'ORACLE_OCM',
#           'USR_MS_UNFIT_CONS', 'USR_MS_OFERTA_SYNC', 'AS_TC', 'USR_MS_MEDICO', 'USR_MS_FIDELIDADE_SYNC',
#           'CTMSERVICE', 'USR_MS_MKTP_INTEGRA', 'USR_MS_MKTP_VENDEDOR_PRD', 'USR_MS_FUNCIONARIO_PRD',
#           'USR_MS_MKTP_FINANCEIRO_PRD', 'USR_ZABBIX_V8', 'USR_MS_MKTP_INTEGRA_PRD',  'AVUSER',
#           'USR_MS_MEDICO_PRD', 'USROFERTAS', 'USR_MS_MKTP_CATALOGO', 'USR_MS_MKTP_PEDIDO', 'USR_DELPHIX',
#           'USR_MS_MKTP_CATALOGO_PRD', 'USR_SOLIC', 'USR_MS_MKTP_PEDIDO_PRD', 'USR_DELPHIX2'}


def generate_object_index_keys(owners, object_types, origin):
    keys = {}
    for owner in owners:
        keys[owner] = {}
        for obj_type in object_types:
            obj_enum = OracleCodeObjectType[obj_type]
            keys[owner][obj_type] = ObjectIndexKey(origin=origin, namespace=owner, type=obj_enum)
    return keys


if __name__ == '__main__':
    csv_filepath = "../../examples/r102_objects.csv"
    origin = Origin(name="R102", description="R102 oracle database instance", type=OriginType.ORACLE_DB)
    objects = get_oracle_objects_from_csv(origin=origin,
                                          csv_filepath=csv_filepath)

    idx = generate_index(objects)

    keys = generate_object_index_keys(OWNERS, OBJECT_TYPES, origin)

    # a_raia_bd_table_item_key = ObjectIndexKey(origin=origin,
    #                                           namespace="A_RAIABD",
    #                                           type=OracleCodeObjectType.TABLE)


    root_directory = Path("../../examples/PortalTC-Core-master")
    # root_directory = Path("../../examples/rd-estoque-master")
    result = []
    for owner in keys:
        for obj_type in keys[owner]:
            print(keys[owner][obj_type])
            result.extend(find_tokens_java(root_directory, idx.get_item(keys[owner][obj_type])))

    write_csv_from_token_info(result, '../../output/token_java.csv')
