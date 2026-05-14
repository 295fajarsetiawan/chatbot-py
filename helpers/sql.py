import re


# Daftar kata SQL yang tidak boleh dipakai oleh chatbot.
FORBIDDEN_SQL = re.compile(
    r"\b(alter|drop|create|truncate|replace|grant|revoke|call|load|outfile|infile)\b",
    re.IGNORECASE,
)
READ_OPERATIONS = {"select", "with"}
WRITE_OPERATIONS = {"insert", "update", "delete"}
CHAT_OPERATIONS = READ_OPERATIONS | WRITE_OPERATIONS


def clean_sql(sql: str) -> str:
    """Membersihkan SQL dari whitespace, semicolon akhir, dan markdown code block."""
    # Hilangkan whitespace dan pagar markdown jika model membungkus query dengan code block.
    cleaned = sql.strip()
    cleaned = re.sub(r"^```sql", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    # Semicolon terakhir boleh dihapus, tapi semicolon di tengah dianggap multi-statement.
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if ";" in cleaned:
        raise ValueError("SQL tidak boleh berisi lebih dari satu statement.")

    return cleaned


def get_sql_operation(sql: str) -> str:
    """Mengambil command utama dari SQL, misalnya select, insert, update, atau delete."""
    match = re.match(r"^\s*([a-zA-Z]+)\b", sql)
    if not match:
        raise ValueError("SQL kosong atau tidak valid.")
    return match.group(1).lower()


def validate_read_only_sql(sql: str) -> str:
    """Memastikan SQL dari AI hanya query baca data."""
    cleaned = clean_sql(sql)
    operation = get_sql_operation(cleaned)

    # Chatbot hanya boleh membaca data, bukan mengubah struktur atau isi database.
    if operation not in READ_OPERATIONS:
        raise ValueError("Hanya query SELECT atau WITH yang diizinkan.")
    if FORBIDDEN_SQL.search(cleaned):
        raise ValueError("Query mengandung perintah yang tidak diizinkan.")

    return cleaned


def validate_chat_sql(sql: str) -> str:
    """Memastikan SQL chat hanya SELECT/WITH/INSERT/UPDATE/DELETE yang aman."""
    cleaned = clean_sql(sql)
    operation = get_sql_operation(cleaned)

    if operation not in CHAT_OPERATIONS:
        raise ValueError("Chat hanya mendukung SELECT, INSERT, UPDATE, atau DELETE.")
    if FORBIDDEN_SQL.search(cleaned):
        raise ValueError("Query mengandung perintah yang tidak diizinkan.")

    # UPDATE/DELETE tanpa WHERE terlalu berisiko karena bisa mengubah semua baris.
    if operation in {"update", "delete"} and not re.search(r"\bwhere\b", cleaned, re.IGNORECASE):
        raise ValueError("Query UPDATE atau DELETE wajib memiliki klausa WHERE.")

    return cleaned


def is_result_query(sql: str) -> bool:
    """Menentukan apakah SQL menghasilkan tabel data."""
    return get_sql_operation(sql) in READ_OPERATIONS


def enforce_limit(sql: str, max_rows: int) -> str:
    """Menambahkan LIMIT jika query belum membatasi jumlah baris."""
    if not is_result_query(sql):
        return sql
    if re.search(r"\blimit\s+\d+\b", sql, re.IGNORECASE):
        return sql
    return f"{sql} LIMIT {max_rows}"
