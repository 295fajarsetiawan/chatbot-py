import re
from dataclasses import dataclass
from typing import List, Optional


BLOCKED_IMPORT_SQL = re.compile(r"^\s*(drop|truncate|delete|update)\b", re.IGNORECASE)
CREATE_DATABASE_SQL = re.compile(r"^\s*create\s+database\b", re.IGNORECASE)
CREATE_TABLE_SQL = re.compile(r"^\s*create\s+table\s+(?!if\s+not\s+exists\b)", re.IGNORECASE)
INSERT_SQL = re.compile(r"^\s*insert\s+into\b", re.IGNORECASE)
INSERT_WITH_COLUMNS_SQL = re.compile(
    r"^\s*insert(?:\s+ignore)?\s+into\s+(?P<table>`[^`]+`|[a-zA-Z0-9_]+)\s*"
    r"\((?P<columns>.*?)\)\s+values\s*(?P<values>.*)$",
    re.IGNORECASE | re.DOTALL,
)
USE_DATABASE_SQL = re.compile(r"^\s*use\b", re.IGNORECASE)


@dataclass
class PreparedSqlStatement:
    sql: Optional[str]
    skipped: bool = False
    reason: str = ""


@dataclass
class InsertStatementInfo:
    columns: List[str]
    rows: List[List[str]]
    table_name: str


def decode_sql_upload(uploaded_file) -> str:
    """Membaca file SQL upload dan mengubah bytes menjadi string."""
    raw_content = uploaded_file.getvalue()

    # Umumnya dump SQL memakai UTF-8, tapi fallback latin-1 membuat file lama tetap terbaca.
    try:
        return raw_content.decode("utf-8")
    except UnicodeDecodeError:
        return raw_content.decode("latin-1")


def split_sql_statements(script: str) -> List[str]:
    """Memecah SQL script menjadi statement terpisah tanpa merusak string literal."""
    statements = []
    buffer = []
    quote = None
    escaped = False
    in_line_comment = False
    in_block_comment = False
    index = 0

    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""

        # Komentar satu baris dibuang sampai newline.
        if in_line_comment:
            if char in "\r\n":
                in_line_comment = False
                buffer.append(char)
            index += 1
            continue

        # Komentar block seperti /* ... */ dibuang seluruhnya.
        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        # Saat berada di dalam quote, semicolon dianggap bagian dari value.
        if quote:
            buffer.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                # MySQL juga mengizinkan quote ganda, misalnya 'it''s'.
                if next_char == quote:
                    buffer.append(next_char)
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if char == "-" and next_char == "-" and _is_mysql_line_comment(script, index):
            in_line_comment = True
            index += 2
            continue
        if char == "#":
            in_line_comment = True
            index += 1
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue
        if char in ("'", '"', "`"):
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue

        buffer.append(char)
        index += 1

    statement = "".join(buffer).strip()
    if statement:
        statements.append(statement)

    return statements


def prepare_import_statement(
    statement: str,
    create_table_if_not_exists: bool = True,
    insert_ignore: bool = False,
) -> PreparedSqlStatement:
    """Menyiapkan statement SQL agar aman untuk mode import aplikasi."""
    sql = statement.strip()

    if not sql:
        return PreparedSqlStatement(sql=None, skipped=True, reason="Statement kosong.")

    # Import diarahkan ke database yang dipilih di sidebar, jadi USE/CREATE DATABASE dilewati.
    if USE_DATABASE_SQL.search(sql):
        return PreparedSqlStatement(sql=None, skipped=True, reason="Statement USE dilewati.")
    if CREATE_DATABASE_SQL.search(sql):
        return PreparedSqlStatement(
            sql=None,
            skipped=True,
            reason="Statement CREATE DATABASE dilewati.",
        )

    # Hindari aksi destruktif saat user hanya ingin import data/schema.
    if BLOCKED_IMPORT_SQL.search(sql):
        return PreparedSqlStatement(
            sql=None,
            skipped=True,
            reason="Statement destruktif dilewati.",
        )

    if create_table_if_not_exists:
        sql = CREATE_TABLE_SQL.sub("CREATE TABLE IF NOT EXISTS ", sql, count=1)

    if insert_ignore:
        sql = INSERT_SQL.sub("INSERT IGNORE INTO", sql, count=1)

    return PreparedSqlStatement(sql=sql)


def parse_insert_statement(statement: str) -> Optional[InsertStatementInfo]:
    """Mengambil nama tabel, kolom, dan value dari INSERT yang memakai daftar kolom."""
    match = INSERT_WITH_COLUMNS_SQL.search(statement.strip())
    if not match:
        return None

    table_name = _clean_identifier(match.group("table"))
    columns = [_clean_identifier(column) for column in split_top_level_commas(match.group("columns"))]
    rows = [
        split_top_level_commas(row)
        for row in _extract_value_groups(match.group("values"))
    ]

    if not table_name or not columns or not rows:
        return None

    return InsertStatementInfo(
        columns=columns,
        rows=rows,
        table_name=table_name,
    )


def infer_mysql_type_from_sql_values(values: List[str]) -> str:
    """Menebak tipe kolom MySQL dari literal value pada INSERT SQL."""
    non_null_values = [
        value.strip()
        for value in values
        if value.strip().lower() not in {"null", "default"}
    ]

    if not non_null_values:
        return "TEXT"

    if all(_is_integer_literal(value) for value in non_null_values):
        return "BIGINT"

    if all(_is_number_literal(value) for value in non_null_values):
        return "DOUBLE"

    max_length = max(len(_unquote_sql_string(value)) for value in non_null_values)
    if max_length <= 255:
        return "VARCHAR(255)"
    return "TEXT"


def split_top_level_commas(text: str) -> List[str]:
    """Memecah teks berdasarkan koma yang tidak berada di dalam quote atau kurung."""
    parts = []
    buffer = []
    quote = None
    escaped = False
    depth = 0

    for char in text:
        if quote:
            buffer.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in ("'", '"', "`"):
            quote = char
            buffer.append(char)
            continue
        if char == "(":
            depth += 1
            buffer.append(char)
            continue
        if char == ")":
            depth = max(depth - 1, 0)
            buffer.append(char)
            continue
        if char == "," and depth == 0:
            parts.append("".join(buffer).strip())
            buffer = []
            continue

        buffer.append(char)

    last_part = "".join(buffer).strip()
    if last_part:
        parts.append(last_part)

    return parts


def _extract_value_groups(values_sql: str) -> List[str]:
    groups = []
    buffer = []
    quote = None
    escaped = False
    depth = 0

    for char in values_sql.strip():
        if quote:
            buffer.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in ("'", '"'):
            quote = char
            buffer.append(char)
            continue
        if char == "(":
            if depth > 0:
                buffer.append(char)
            depth += 1
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                groups.append("".join(buffer).strip())
                buffer = []
            else:
                buffer.append(char)
            continue

        if depth > 0:
            buffer.append(char)

    return groups


def _clean_identifier(identifier: str) -> str:
    identifier = identifier.strip()
    if identifier.startswith("`") and identifier.endswith("`"):
        return identifier[1:-1].replace("``", "`")
    return identifier


def _is_mysql_line_comment(script: str, index: int) -> bool:
    """Komentar -- MySQL valid jika setelahnya whitespace atau akhir file."""
    after_dash = index + 2
    return after_dash >= len(script) or script[after_dash].isspace()


def _is_integer_literal(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?\d+", value.strip()))


def _is_number_literal(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value.strip()))


def _unquote_sql_string(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] in {"'", '"'} and stripped[-1] == stripped[0]:
        return stripped[1:-1].replace(stripped[0] * 2, stripped[0])
    return stripped
