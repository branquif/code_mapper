import csv
import yaml
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.sqlite import insert
from pathlib import Path
import argparse


# Pydantic classes
class ColumnMapping(BaseModel):
    name: str
    type: str | None = None


class CSVFileInfo(BaseModel):
    csv_file: Path
    separator: str
    has_header: bool
    table_name: str
    column_order: list[str] | None = None
    exclude_columns: list[str] = None  # New field for excluded columns
    column_mapping: dict[str, ColumnMapping]


class Config(BaseModel):
    database_uri: str
    csv_files_info: list[CSVFileInfo]


def bulk_upsert(csv_file_info: CSVFileInfo, engine, batch_size: int = 1000):
    metadata = MetaData()
    table = Table(csv_file_info.table_name, metadata, autoload_with=engine)
    keys = [key.name.lower() for key in table.primary_key.columns]

    exclude_columns = [column.lower() for column in (csv_file_info.exclude_columns or [])]
    column_mapping_lower = {k.lower(): v for k, v in csv_file_info.column_mapping.items()}

    with csv_file_info.csv_file.open('r', newline='', encoding='utf-8') as file:
        if csv_file_info.has_header:
            reader = csv.DictReader(file, delimiter=csv_file_info.separator)
            if reader.fieldnames:
                reader.fieldnames = [name.lower() for name in reader.fieldnames]
        else:
            reader = csv.reader(file, delimiter=csv_file_info.separator)
            if reader.fieldnames:
                column_order_lower = [col.lower() for col in csv_file_info.column_order]
                reader = (dict(zip(column_order_lower, row)) for row in reader)

        batch_data = []
        for row in reader:
            row_data = {}
            for col in row:
                col_lower = col.lower()
                if col_lower not in exclude_columns:
                    if col_lower in column_mapping_lower:
                        mapped_col = column_mapping_lower[col_lower].name
                    else:
                        mapped_col = col

                    # Set empty strings to None for NULL representation in the database
                    row_data[mapped_col] = row[col] if row[col] != '' else None

            batch_data.append(row_data)

            if len(batch_data) >= batch_size:
                execute_batch_upsert(batch_data, table, keys, engine)
                batch_data = []

        if batch_data:
            execute_batch_upsert(batch_data, table, keys, engine)


def execute_batch_upsert(batch_data, table, keys, engine):
    stmt = insert(table)
    update_dict = {c.name: c for c in stmt.excluded if not c.primary_key}
    upsert_stmt = stmt.on_conflict_do_update(index_elements=keys, set_=update_dict).values(batch_data)

    with engine.begin() as conn:
        conn.execute(upsert_stmt)


def main(config_path: Path):
    with open(config_path, 'r') as file:
        config_data = yaml.safe_load(file)
    config = Config(**config_data)

    engine = create_engine(config.database_uri)

    for csv_file_info in config.csv_files_info:
        bulk_upsert(csv_file_info, engine)

    print("Data uploaded successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Upsert CSV data into a Database")
    parser.add_argument("config", type=Path, help="Path to the YAML configuration file")
    args = parser.parse_args()
    main(args.config)
