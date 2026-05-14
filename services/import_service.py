from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from helpers.dataframe import clean_dataframe_columns, read_uploaded_table
from helpers.identifiers import normalize_identifier
from helpers.sql_script import decode_sql_upload, split_sql_statements
from repositories.mysql_repository import MySqlRepository


@dataclass
class ImportPreview:
    dataframe: pd.DataFrame
    column_mapping: Dict[str, str]
    table_name: str


@dataclass
class ImportResult:
    created_columns: List[str]
    created_table: bool
    inserted: int


@dataclass
class SqlImportPreview:
    file_name: str
    script: str
    statements: List[str]


@dataclass
class SqlImportResult:
    created_columns: Dict[str, List[str]]
    created_tables: List[str]
    executed: int
    skipped_reasons: List[str]


class ImportService:
    def __init__(self, repository: MySqlRepository):
        self.repository = repository

    def prepare_upload(self, uploaded_file, raw_table_name: str) -> ImportPreview:
        raw_df = read_uploaded_table(uploaded_file)
        cleaned_df, column_mapping = clean_dataframe_columns(raw_df)
        table_name = normalize_identifier(raw_table_name, "import_data")

        return ImportPreview(
            dataframe=cleaned_df,
            column_mapping=column_mapping,
            table_name=table_name,
        )

    def prepare_sql_upload(self, uploaded_file) -> SqlImportPreview:
        script = decode_sql_upload(uploaded_file)
        statements = split_sql_statements(script)

        if not statements:
            raise ValueError("File SQL tidak memiliki statement yang bisa dijalankan.")

        return SqlImportPreview(
            file_name=uploaded_file.name,
            script=script,
            statements=statements,
        )

    def import_preview(self, preview: ImportPreview) -> ImportResult:
        connection = self.repository.connect()
        try:
            import_df, created_columns, created_table = (
                self.repository.ensure_table_for_dataframe(
                    connection,
                    preview.table_name,
                    preview.dataframe,
                )
            )
            inserted = self.repository.insert_dataframe(
                connection,
                preview.table_name,
                import_df,
            )
            return ImportResult(
                created_columns=created_columns,
                created_table=created_table,
                inserted=inserted,
            )
        finally:
            connection.close()

    def import_sql_preview(
        self,
        preview: SqlImportPreview,
        auto_create_tables: bool = True,
        create_table_if_not_exists: bool = True,
        insert_ignore: bool = False,
    ) -> SqlImportResult:
        connection = self.repository.connect()
        try:
            executed, skipped_reasons, created_tables, created_columns = (
                self.repository.execute_sql_import(
                    connection,
                    preview.statements,
                    auto_create_tables=auto_create_tables,
                    create_table_if_not_exists=create_table_if_not_exists,
                    insert_ignore=insert_ignore,
                )
            )
            return SqlImportResult(
                created_columns=created_columns,
                created_tables=created_tables,
                executed=executed,
                skipped_reasons=skipped_reasons,
            )
        finally:
            connection.close()
