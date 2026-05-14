from dataclasses import dataclass
from typing import Optional

import pandas as pd

from repositories.mysql_repository import MySqlRepository
from services.ollama_service import OllamaService


@dataclass
class ChatResult:
    affected_rows: int
    dataframe: Optional[pd.DataFrame]
    explanation: str
    operation: str
    sql: str


class ChatService:
    def __init__(self, repository: MySqlRepository, ollama_service: OllamaService):
        self.repository = repository
        self.ollama_service = ollama_service

    def ask(self, question: str, max_rows: int) -> ChatResult:
        connection = self.repository.connect()
        try:
            schema = self.repository.get_schema_summary(connection)
            generated = self.ollama_service.create_sql(question, schema)
            execution = self.repository.execute_chat_sql(
                connection,
                generated.sql,
                max_rows,
            )

            try:
                if execution.dataframe is not None:
                    explanation = self.ollama_service.describe_result(
                        question,
                        execution.sql,
                        execution.dataframe,
                    )
                else:
                    explanation = self.ollama_service.describe_change(
                        question,
                        execution.sql,
                        execution.operation,
                        execution.affected_rows,
                    )
            except Exception:
                explanation = self._fallback_description(
                    execution.operation,
                    execution.dataframe,
                    execution.affected_rows,
                )

            return ChatResult(
                affected_rows=execution.affected_rows,
                dataframe=execution.dataframe,
                explanation=explanation,
                operation=execution.operation,
                sql=execution.sql,
            )
        finally:
            connection.close()

    @staticmethod
    def _fallback_description(
        operation: str,
        dataframe: Optional[pd.DataFrame],
        affected_rows: int,
    ) -> str:
        if dataframe is None:
            return (
                f"Perintah {operation.upper()} berhasil dijalankan. "
                f"{affected_rows} baris terdampak."
            )

        if dataframe.empty:
            return "Query berhasil dijalankan, tetapi tidak ada data yang ditemukan."

        columns = ", ".join(str(column) for column in dataframe.columns)
        return (
            f"Hasil query menampilkan {len(dataframe)} baris data "
            f"dengan kolom: {columns}. "
            "Tabel hasilnya bisa dilihat di bawah deskripsi ini."
        )
