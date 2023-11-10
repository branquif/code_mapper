# Java SQL Reference Mapper

This application parses Java files, extracts SQL references and maps them to database objects. It aims to support both JPA and JDBC based queries within a Java project. The output is a CSV file that lists the references along with the file name and line number.

## Structure

The project is structured as follows:

- `antlr_files/`: Contains the ANTLR grammar files and generated parser and lexer files for Java.
- `src/`: Contains the main source code of the Python application.
- `tests/`: Contains unit tests for the application.
- `examples/`: Contains example input files for testing the application.
- `output/`: The directory where output CSV files are written.

## Setup

Ensure you have [Poetry](https://python-poetry.org/docs/) installed.

1. Clone the repository:
```bash
git clone https://github.com/your_username/java-sql-reference-mapper.git
cd java-sql-reference-mapper
```

install dependencies:
```bash
poetry install
```

Usage
1. Place your Java files in the examples/java_example1/ and examples/java_example2/ directories.
2. Update examples/db_objects.csv with your database objects.
3. Run the application:
```bash
poetry run python src/your_project_name/main.py
```


# TODO
- [ ] Add support for JPA queries
- [ ] Identify entities within objects
- [ ] Identify JPA repositories and their entities
- [ ] Within JPA repositories, identify the methods and which operations it does on which tables
- [ ] Check if the query is native or JPA generated
- [ ] Add support for JDBC queries
- [ ] Add support for Spring Data JPA queries
- [ ] Add support for Spring JDBC queries
- 