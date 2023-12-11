import sqlite3
from typing import List, Any
from jinja2 import Environment, FileSystemLoader
from typing import Dict
from pathlib import Path
import argparse
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Domain(Base):
    __tablename__ = 'TB_DOMAIN'

    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    parent_code = Column(String, ForeignKey('TB_DOMAIN.code'))

    # Relationship to self to represent the hierarchy
    parent = relationship('TBDomain', remote_side=[code], backref='children')

    # Relationship to TBComponent
    components = relationship('TBComponent', backref='domain')

    def __repr__(self):
        return f"<TBDomain(code='{self.code}', name='{self.name}')>"


class TBComponent(Base):
    __tablename__ = 'TB_COMPONENT'

    code = Column(String, primary_key=True)
    name = Column(String)
    domain_code = Column(String, ForeignKey('TB_DOMAIN.code'))
    type = Column(String)
    parent_code = Column(String, ForeignKey('TB_COMPONENT.code'))

    # Relationship to self to represent the hierarchy
    parent = relationship('TBComponent', remote_side=[code], backref='children')

    def __repr__(self):
        return f"<TBComponent(code='{self.code}', name='{self.name}')>"


class TBCodeObject(Base):
    __tablename__ = 'TB_CODE_OBJECT'

    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    source_file = Column(String)
    system_component_code = Column(String, ForeignKey('TB_COMPONENT.code'))

    # Relationship to TBComponent
    component = relationship('TBComponent', backref='code_objects')

    def __repr__(self):
        return f"<TBCodeObject(code='{self.code}', name='{self.name}')>"

# Replace with your database URL
engine = create_engine('sqlite:///path_to_your_database.db')

Session = sessionmaker(bind=engine)
session = Session()

# Example query
domains = session.query(TBDomain).all()
for domain in domains:
    print(domain)


def read_sql_file(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read()


def execute_query(db_path: str, query_file: str) -> List[Any]:
    query = read_sql_file(query_file)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def generate_structurizr_dsl(template_path: str, data: Dict) -> str:
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_path)
    return template.render(data)


def main():
    parser = argparse.ArgumentParser(description="Generate Structurizr DSL from SQLite data.")
    parser.add_argument("--db", required=True, help="Path to the SQLite database file.")
    parser.add_argument("--query", required=True, help="SQL query file name.")
    parser.add_argument("--template", required=True, help="Jinja2 template file name for Structurizr DSL.")
    args = parser.parse_args()

    # Read and execute query
    data = execute_query(args.db, args.query)

    # Generate Structurizr DSL
    dsl_code = generate_structurizr_dsl(args.template, {"data": data})
    print(dsl_code)


if __name__ == "__main__":
    # main()
    data = execute_query(Path("../../data/rd.db"), Path("queries/domain.sql"))
    print(data)