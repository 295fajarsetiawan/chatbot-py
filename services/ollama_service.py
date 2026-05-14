import json
import re
from dataclasses import dataclass
from typing import Dict

import pandas as pd
import requests


@dataclass
class GeneratedSql:
    explanation: str
    sql: str


class OllamaService:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def create_sql(self, question: str, schema_summary: str) -> GeneratedSql:
        response = requests.post(
            self.base_url + "/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._user_prompt(question, schema_summary)},
                ],
                "options": {"temperature": 0},
            },
            timeout=90,
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content") or data.get("response", "")
        parsed = self.parse_response(content)

        return GeneratedSql(
            explanation=parsed.get("explanation", ""),
            sql=parsed.get("sql", ""),
        )

    def describe_result(self, question: str, sql: str, dataframe: pd.DataFrame) -> str:
        sample = dataframe.head(20).to_dict(orient="records")
        columns = list(dataframe.columns)

        response = requests.post(
            self.base_url + "/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Kamu adalah asisten data. Jelaskan hasil query database "
                            "dalam Bahasa Indonesia yang singkat, jelas, dan mudah dipahami. "
                            "Jangan membuat data baru. Jika hasil kosong, jelaskan bahwa data tidak ditemukan."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Pertanyaan user: {question}\n"
                            f"SQL yang dijalankan: {sql}\n"
                            f"Jumlah baris hasil yang ditampilkan: {len(dataframe)}\n"
                            f"Kolom: {columns}\n"
                            f"Sample data JSON: {json.dumps(sample, default=str, ensure_ascii=False)}\n\n"
                            "Buat deskripsi hasil dalam 2-4 kalimat."
                        ),
                    },
                ],
                "options": {"temperature": 0.2},
            },
            timeout=90,
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content") or data.get("response", "")
        return content.strip()

    def describe_change(
        self,
        question: str,
        sql: str,
        operation: str,
        affected_rows: int,
    ) -> str:
        response = requests.post(
            self.base_url + "/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Kamu adalah asisten database. Jelaskan hasil perintah "
                            "INSERT, UPDATE, atau DELETE dalam Bahasa Indonesia yang singkat. "
                            "Sebutkan jenis aksi dan jumlah baris terdampak. "
                            "Jangan mengarang data yang tidak ada."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Pertanyaan user: {question}\n"
                            f"Operasi: {operation.upper()}\n"
                            f"SQL yang dijalankan: {sql}\n"
                            f"Jumlah baris terdampak: {affected_rows}\n\n"
                            "Buat informasi hasil dalam 1-3 kalimat."
                        ),
                    },
                ],
                "options": {"temperature": 0.2},
            },
            timeout=90,
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content") or data.get("response", "")
        return content.strip()

    @staticmethod
    def parse_response(content: str) -> Dict[str, str]:
        text = content.strip()
        text = re.sub(r"^```(?:json|sql)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                parsed = json.loads(text[start : end + 1])
            else:
                parsed = {"sql": text, "explanation": "Query dibuat dari respons model."}

        return {
            "sql": str(parsed.get("sql", "")).strip(),
            "explanation": str(parsed.get("explanation", "")).strip(),
        }

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Kamu adalah asisten SQL MySQL untuk membaca dan mengubah data. "
            "Gunakan hanya tabel dan kolom pada schema yang diberikan. "
            "Balas JSON valid saja dengan key sql dan explanation. "
            "SQL wajib satu statement saja, tanpa semicolon dan tanpa komentar. "
            "Statement yang boleh dibuat: SELECT, WITH, INSERT, UPDATE, DELETE. "
            "Jangan pernah membuat ALTER, DROP, CREATE, TRUNCATE, REPLACE, LOAD, CALL, GRANT, REVOKE. "
            "Untuk UPDATE dan DELETE wajib memakai WHERE yang spesifik. "
            "Jika user meminta daftar data, tambahkan LIMIT yang wajar. "
            "Jika user meminta tambah data, gunakan INSERT. "
            "Jika user meminta ubah data, gunakan UPDATE dengan WHERE. "
            "Jika user meminta hapus data, gunakan DELETE dengan WHERE."
        )

    @staticmethod
    def _user_prompt(question: str, schema_summary: str) -> str:
        return (
            "Schema database:\n"
            f"{schema_summary}\n\n"
            "Pertanyaan user:\n"
            f"{question}\n"
        )
