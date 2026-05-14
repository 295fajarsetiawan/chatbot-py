from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import mysql.connector
import pandas as pd

from helpers.dataframe import infer_mysql_type, to_mysql_value
from helpers.identifiers import quote_identifier
from helpers.sql import (
    enforce_limit,
    get_sql_operation,
    is_result_query,
    validate_chat_sql,
    validate_read_only_sql,
)
from helpers.sql_script import (
    infer_mysql_type_from_sql_values,
    parse_insert_statement,
    prepare_import_statement,
)


@dataclass
class SqlExecutionResult:
    affected_rows: int
    dataframe: Optional[pd.DataFrame]
    operation: str
    sql: str


class MySqlRepository:
    """Repository untuk semua operasi database MySQL."""

    def __init__(self, config: Dict[str, Any]):
        # Config berasal dari sidebar Streamlit atau environment variable.
        self.config = config

    @property
    def database(self) -> str:
        # Nama database sering dipakai, jadi dibuat property agar lebih ringkas.
        return self.config["database"]

    def connect(self):
        """Membuka koneksi MySQL dan memilih database yang akan dipakai."""
        if not self.database:
            raise ValueError("Nama database wajib diisi.")

        # Koneksi dibuat tanpa autocommit agar insert/alter bisa di-rollback saat error.
        connection = mysql.connector.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            autocommit=False,
        )

        cursor = connection.cursor()
        try:
            # Opsi ini memudahkan user pertama kali menjalankan aplikasi.
            if self.config["create_database"]:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {quote_identifier(self.database)} "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                connection.commit()

            # Setelah database tersedia, semua query berikutnya diarahkan ke database ini.
            cursor.execute(f"USE {quote_identifier(self.database)}")
        finally:
            cursor.close()

        return connection

    def table_exists(self, connection, table_name: str) -> bool:
        """Mengecek apakah tabel tujuan sudah ada di database."""
        cursor = connection.cursor()
        try:
            # information_schema dipakai agar pengecekan tidak bergantung pada error MySQL.
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                """,
                (self.database, table_name),
            )
            return bool(cursor.fetchone()[0])
        finally:
            cursor.close()

    def get_existing_columns(self, connection, table_name: str) -> List[str]:
        """Mengambil daftar kolom yang sudah ada pada tabel."""
        cursor = connection.cursor()
        try:
            # Urutan kolom asli dipertahankan supaya schema summary mudah dibaca.
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (self.database, table_name),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def ensure_table_for_dataframe(
        self,
        connection,
        table_name: str,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[str], bool]:
        """Membuat tabel/kolom yang belum ada sebelum data diinsert."""
        cursor = connection.cursor()
        created_columns = []
        created_table = False

        try:
            # Jika tabel belum ada, buat tabel baru dari struktur dataframe upload.
            if not self.table_exists(connection, table_name):
                primary_key = "_import_id"
                counter = 1

                # Hindari tabrakan jika file upload ternyata punya kolom bernama _import_id.
                while primary_key in df.columns:
                    counter += 1
                    primary_key = f"_import_id_{counter}"

                # Primary key internal dibuat otomatis supaya setiap row punya identifier.
                column_sql = [
                    f"{quote_identifier(primary_key)} BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY"
                ]

                # Tipe data MySQL ditebak dari tipe kolom pandas.
                for column in df.columns:
                    column_sql.append(
                        f"{quote_identifier(column)} {infer_mysql_type(df[column])} NULL"
                    )

                # Nama tabel dan kolom selalu di-quote untuk menghindari bentrok keyword SQL.
                cursor.execute(
                    f"CREATE TABLE {quote_identifier(table_name)} ("
                    + ", ".join(column_sql)
                    + ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
                )
                connection.commit()
                created_table = True
                created_columns = list(df.columns)
                return df, created_columns, created_table

            existing_columns = self.get_existing_columns(connection, table_name)

            # Samakan kapitalisasi nama kolom upload dengan kolom lama jika sebenarnya sama.
            df = self._align_to_existing_columns(df, existing_columns)
            existing_lower = {column.lower() for column in existing_columns}

            # Untuk tabel yang sudah ada, hanya kolom baru yang ditambahkan.
            for column in df.columns:
                if column.lower() not in existing_lower:
                    cursor.execute(
                        f"ALTER TABLE {quote_identifier(table_name)} "
                        f"ADD COLUMN {quote_identifier(column)} {infer_mysql_type(df[column])} NULL"
                    )
                    created_columns.append(column)
                    existing_lower.add(column.lower())

            if created_columns:
                connection.commit()

            return df, created_columns, created_table
        finally:
            cursor.close()

    def insert_dataframe(
        self,
        connection,
        table_name: str,
        df: pd.DataFrame,
        batch_size: int = 1000,
    ) -> int:
        """Insert seluruh isi dataframe ke tabel tujuan secara bertahap."""
        if df.empty:
            return 0

        columns = list(df.columns)

        # Query insert dibuat dinamis mengikuti kolom dataframe hasil upload.
        quoted_columns = ", ".join(quote_identifier(column) for column in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = (
            f"INSERT INTO {quote_identifier(table_name)} ({quoted_columns}) "
            f"VALUES ({placeholders})"
        )

        # Nilai pandas/numpy diubah ke tipe Python standar agar diterima MySQL connector.
        rows = [
            tuple(to_mysql_value(value) for value in row)
            for row in df.itertuples(index=False, name=None)
        ]

        cursor = connection.cursor()
        inserted = 0
        try:
            # Batch insert mencegah query terlalu besar saat file upload punya banyak baris.
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                cursor.executemany(insert_sql, batch)
                inserted += cursor.rowcount
            connection.commit()
            return inserted
        except Exception:
            # Jika salah satu batch gagal, semua perubahan insert dibatalkan.
            connection.rollback()
            raise
        finally:
            cursor.close()

    def get_schema_summary(self, connection) -> str:
        """Membuat ringkasan schema untuk dikirim ke model Ollama."""
        cursor = connection.cursor(dictionary=True)
        try:
            # Ringkasan hanya berisi nama tabel, nama kolom, dan tipe kolom.
            cursor.execute(
                """
                SELECT
                    table_name AS table_name,
                    column_name AS column_name,
                    column_type AS column_type
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (self.database,),
            )
            grouped = {}

            # Data schema dikelompokkan per tabel agar prompt AI lebih ringkas.
            for row in cursor.fetchall():
                table_name = self._dict_value(row, "table_name", "TABLE_NAME")
                column_name = self._dict_value(row, "column_name", "COLUMN_NAME")
                column_type = self._dict_value(row, "column_type", "COLUMN_TYPE")

                grouped.setdefault(table_name, []).append(
                    f"{column_name} {column_type}"
                )

            if not grouped:
                return "Belum ada tabel pada database ini."

            lines = []
            for table, columns in grouped.items():
                lines.append(f"{table}: " + ", ".join(columns))
            return "\n".join(lines)
        finally:
            cursor.close()

    def list_tables(self, connection) -> List[str]:
        """Mengambil daftar tabel untuk tampilan tab Schema."""
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
                """,
                (self.database,),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def query_dataframe(
        self,
        connection,
        sql: str,
        max_rows: int,
    ) -> Tuple[pd.DataFrame, str]:
        """Menjalankan query baca data dan mengembalikan hasil sebagai dataframe."""
        # Query dari AI divalidasi ulang di backend sebelum dikirim ke MySQL.
        safe_sql = enforce_limit(validate_read_only_sql(sql), max_rows)
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(safe_sql)
            rows = cursor.fetchmany(max_rows)
            return pd.DataFrame(rows), safe_sql
        finally:
            cursor.close()

    def execute_chat_sql(
        self,
        connection,
        sql: str,
        max_rows: int,
    ) -> SqlExecutionResult:
        """Menjalankan SQL dari chat, baik query baca maupun perubahan data."""
        safe_sql = validate_chat_sql(sql)
        operation = get_sql_operation(safe_sql)

        if is_result_query(safe_sql):
            safe_sql = enforce_limit(safe_sql, max_rows)
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(safe_sql)
                rows = cursor.fetchmany(max_rows)
                dataframe = pd.DataFrame(rows)
                return SqlExecutionResult(
                    affected_rows=len(dataframe),
                    dataframe=dataframe,
                    operation=operation,
                    sql=safe_sql,
                )
            finally:
                cursor.close()

        cursor = connection.cursor()
        try:
            cursor.execute(safe_sql)
            affected_rows = max(cursor.rowcount, 0)
            connection.commit()
            return SqlExecutionResult(
                affected_rows=affected_rows,
                dataframe=None,
                operation=operation,
                sql=safe_sql,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()

    def execute_sql_import(
        self,
        connection,
        statements: List[str],
        auto_create_tables: bool = True,
        create_table_if_not_exists: bool = True,
        insert_ignore: bool = False,
    ) -> Tuple[int, List[str], List[str], Dict[str, List[str]]]:
        """Menjalankan daftar statement SQL untuk kebutuhan import file .sql."""
        cursor = connection.cursor()
        created_columns_by_table = {}
        created_tables = []
        executed = 0
        skipped_reasons = []

        try:
            for statement in statements:
                prepared = prepare_import_statement(
                    statement,
                    create_table_if_not_exists=create_table_if_not_exists,
                    insert_ignore=insert_ignore,
                )

                # Beberapa statement dump dilewati agar import tetap berada di database aktif.
                if prepared.skipped:
                    skipped_reasons.append(prepared.reason)
                    continue

                if auto_create_tables:
                    created_table, created_columns = self.ensure_table_for_insert_sql(
                        connection,
                        prepared.sql,
                    )
                    if created_table:
                        created_tables.append(created_table)
                    if created_columns:
                        table_name = created_table or parse_insert_statement(prepared.sql).table_name
                        created_columns_by_table.setdefault(table_name, []).extend(created_columns)

                cursor.execute(prepared.sql)
                executed += 1

            connection.commit()
            return executed, skipped_reasons, created_tables, created_columns_by_table
        except Exception:
            # Rollback membantu untuk INSERT, walaupun sebagian DDL MySQL auto-commit.
            connection.rollback()
            raise
        finally:
            cursor.close()

    def ensure_table_for_insert_sql(
        self,
        connection,
        sql: str,
    ) -> Tuple[Optional[str], List[str]]:
        """Membuat tabel/kolom otomatis untuk file SQL yang hanya berisi INSERT."""
        insert_info = parse_insert_statement(sql)
        if insert_info is None:
            return None, []

        column_types = self._infer_insert_column_types(insert_info.columns, insert_info.rows)

        if not self.table_exists(connection, insert_info.table_name):
            primary_key = "_import_id"
            counter = 1
            while primary_key in insert_info.columns:
                counter += 1
                primary_key = f"_import_id_{counter}"

            column_sql = [
                f"{quote_identifier(primary_key)} BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY"
            ]
            for column in insert_info.columns:
                column_sql.append(f"{quote_identifier(column)} {column_types[column]} NULL")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"CREATE TABLE {quote_identifier(insert_info.table_name)} ("
                    + ", ".join(column_sql)
                    + ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
                )
                connection.commit()
            finally:
                cursor.close()

            return insert_info.table_name, list(insert_info.columns)

        existing_columns = self.get_existing_columns(connection, insert_info.table_name)
        existing_lower = {column.lower() for column in existing_columns}
        created_columns = []

        cursor = connection.cursor()
        try:
            for column in insert_info.columns:
                if column.lower() not in existing_lower:
                    cursor.execute(
                        f"ALTER TABLE {quote_identifier(insert_info.table_name)} "
                        f"ADD COLUMN {quote_identifier(column)} {column_types[column]} NULL"
                    )
                    created_columns.append(column)
                    existing_lower.add(column.lower())

            if created_columns:
                connection.commit()
        finally:
            cursor.close()

        return None, created_columns

    @staticmethod
    def _align_to_existing_columns(
        df: pd.DataFrame,
        existing_columns: List[str],
    ) -> pd.DataFrame:
        """Menyesuaikan nama kolom upload dengan kolom tabel yang sudah ada."""
        existing_by_lower = {column.lower(): column for column in existing_columns}

        # Contoh: kolom upload "nama" akan diarahkan ke kolom tabel "Nama" jika sudah ada.
        rename_map = {
            column: existing_by_lower[column.lower()]
            for column in df.columns
            if column.lower() in existing_by_lower
            and existing_by_lower[column.lower()] != column
        }
        if rename_map:
            return df.rename(columns=rename_map)
        return df

    @staticmethod
    def _dict_value(row: Dict[str, Any], *keys: str) -> Any:
        """Mengambil nilai dict cursor dengan fallback key besar/kecil."""
        for key in keys:
            if key in row:
                return row[key]
        raise KeyError(keys[0])

    @staticmethod
    def _infer_insert_column_types(
        columns: List[str],
        rows: List[List[str]],
    ) -> Dict[str, str]:
        """Menebak tipe kolom dari value pada INSERT SQL."""
        column_types = {}
        for index, column in enumerate(columns):
            values = [
                row[index]
                for row in rows
                if index < len(row)
            ]
            column_types[column] = infer_mysql_type_from_sql_values(values)
        return column_types
