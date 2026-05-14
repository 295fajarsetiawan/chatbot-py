from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Tuple

import pandas as pd

from helpers.identifiers import make_unique, normalize_identifier


def clean_dataframe_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Membersihkan nama kolom dataframe agar aman dipakai sebagai kolom MySQL."""
    # Copy dataframe agar data asli dari upload tidak berubah langsung.
    cleaned = df.copy()

    # Setiap nama kolom dinormalisasi, misalnya "Nama Lengkap" menjadi "nama_lengkap".
    normalized = [
        normalize_identifier(column, f"column_{index + 1}")
        for index, column in enumerate(cleaned.columns)
    ]

    # Jika ada nama yang sama setelah normalisasi, tambahkan suffix angka.
    unique_columns = make_unique(normalized)

    # Mapping dipakai UI untuk menunjukkan perubahan nama kolom kepada user.
    mapping = dict(zip([str(column) for column in cleaned.columns], unique_columns))
    cleaned.columns = unique_columns
    return cleaned, mapping


def infer_mysql_type(series: pd.Series) -> str:
    """Menebak tipe kolom MySQL berdasarkan tipe data pandas."""
    if pd.api.types.is_bool_dtype(series):
        return "TINYINT(1)"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"

    # Untuk text/object, panjang data menentukan VARCHAR atau TEXT.
    non_null = series.dropna()
    if non_null.empty:
        return "TEXT"

    max_length = non_null.astype(str).str.len().max()
    if max_length <= 255:
        return "VARCHAR(255)"
    return "TEXT"


def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    """Membaca file upload Streamlit menjadi dataframe pandas."""
    filename = uploaded_file.name.lower()
    if filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    # sep=None membuat pandas mencoba mendeteksi delimiter CSV secara otomatis.
    return pd.read_csv(uploaded_file, sep=None, engine="python")


def to_mysql_value(value: Any) -> Any:
    """Mengubah nilai pandas/numpy menjadi tipe yang aman untuk MySQL connector."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, (datetime, date, Decimal)):
        return value

    # Nilai numpy scalar punya method item() untuk diubah ke tipe Python biasa.
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return value
    return value
