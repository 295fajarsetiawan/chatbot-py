# Tutorial Membuat Project Chatbot MySQL Ollama

Dokumen ini menjelaskan cara membuat project seperti repository ini dari awal sampai bisa digunakan. Project ini adalah aplikasi Streamlit untuk melakukan chat ke database MySQL memakai model Ollama. User bisa import data CSV, Excel, atau SQL, melihat schema database, lalu bertanya atau memberi perintah data memakai bahasa natural.

## 1. Gambaran Project

Fitur utama:

- Chat bahasa natural ke database MySQL.
- Model Ollama membuat SQL dari pertanyaan user.
- Backend memvalidasi SQL sebelum dijalankan.
- Chat mendukung `SELECT`, `WITH`, `INSERT`, `UPDATE`, dan `DELETE`.
- `UPDATE` dan `DELETE` wajib memiliki `WHERE`.
- Import data dari CSV, Excel, atau SQL.
- Tabel dan kolom bisa dibuat otomatis saat import.
- Tab Schema menampilkan ringkasan tabel dan kolom yang sedang dipakai.

Alur kerja aplikasi:

```text
User
  -> Streamlit UI
  -> ChatService / ImportService
  -> MySqlRepository
  -> MySQL

ChatService
  -> OllamaService
  -> Ollama /api/chat
```

## 2. Prasyarat

Siapkan beberapa komponen berikut:

- Python 3.10 atau lebih baru.
- MySQL server, bisa lokal, Docker, XAMPP, Laragon, Aiven, atau server lain.
- Ollama server yang bisa diakses dari komputer aplikasi.
- Model Ollama, contoh: `qwen2.5:latest`.
- Terminal dan browser.

Untuk Ollama lokal, endpoint default biasanya:

```bash
http://localhost:11434
```

Untuk mengecek Ollama lokal:

```bash
ollama pull qwen2.5:latest
ollama serve
```

Di terminal lain:

```bash
curl http://localhost:11434/api/tags
```

Jika memakai Ollama remote, pastikan URL endpoint bisa diakses dan port `11434` tidak diblokir.

## 3. Membuat Folder Project

Buat folder project baru:

```bash
mkdir chatbot-mysql-ollama
cd chatbot-mysql-ollama
```

Buat struktur folder:

```bash
mkdir -p helpers repositories services ui database docs
touch app.py config.py requirements.txt
touch helpers/dataframe.py helpers/env.py helpers/identifiers.py helpers/sql.py helpers/sql_script.py
touch repositories/mysql_repository.py
touch services/chat_service.py services/import_service.py services/ollama_service.py
touch ui/chat_view.py ui/import_view.py ui/schema_view.py ui/sidebar.py
touch database/mysql.sql database/data.sql
```

Struktur akhirnya:

```text
.
├── app.py
├── config.py
├── requirements.txt
├── database/
│   ├── data.sql
│   └── mysql.sql
├── helpers/
│   ├── dataframe.py
│   ├── env.py
│   ├── identifiers.py
│   ├── sql.py
│   └── sql_script.py
├── repositories/
│   └── mysql_repository.py
├── services/
│   ├── chat_service.py
│   ├── import_service.py
│   └── ollama_service.py
└── ui/
    ├── chat_view.py
    ├── import_view.py
    ├── schema_view.py
    └── sidebar.py
```

## 4. Menginstall Dependency

Buat virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Isi `requirements.txt`:

```text
streamlit>=1.35
mysql-connector-python>=8.4
pandas>=2.2
requests>=2.32
urllib3<2
openpyxl>=3.1
```

Install dependency:

```bash
pip install -r requirements.txt
```

Fungsi dependency:

- `streamlit`: membuat UI web.
- `mysql-connector-python`: koneksi ke MySQL.
- `pandas`: membaca CSV/Excel dan menampilkan dataframe.
- `requests`: request ke endpoint Ollama.
- `openpyxl`: membaca file Excel `.xlsx`.

## 5. Membuat Konfigurasi

Isi `config.py` dengan default konfigurasi:

```python
DEFAULT_OLLAMA_MODEL = "qwen2.5:latest"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

DEFAULT_MYSQL_DATABASE = "chatbot"
DEFAULT_MYSQL_HOST = "localhost"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "root"
```

Di project saat ini, `config.py` sudah berisi default host MySQL dan URL Ollama sesuai environment yang sedang dipakai. Untuk project baru, lebih aman memakai konfigurasi lokal seperti contoh di atas, lalu isi detail koneksi dari sidebar aplikasi atau environment variable.

Environment variable yang didukung:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=password_mysql
export MYSQL_DATABASE=chatbot

export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:latest
```

Catatan penting:

- Jangan commit password database ke source code.
- Password MySQL tidak disimpan permanen oleh aplikasi.
- Jika `create_database` aktif di sidebar, aplikasi akan membuat database jika belum ada.

## 6. Urutan Membuat Kode

Gunakan urutan ini agar implementasi mudah dites bertahap.

### 6.1 Helper Environment

File: `helpers/env.py`

Fungsinya membaca environment variable angka seperti `MYSQL_PORT`. Jika value kosong atau bukan angka, aplikasi memakai nilai default agar tetap jalan.

### 6.2 Helper Identifier

File: `helpers/identifiers.py`

Fungsinya:

- Membuat nama tabel dan kolom aman untuk MySQL.
- Mengganti spasi atau simbol menjadi underscore.
- Mencegah nama kosong atau nama yang diawali angka.
- Membungkus identifier dengan backtick agar tidak bentrok dengan keyword SQL.

Contoh:

```text
Nama Lengkap -> nama_lengkap
2024 Sales   -> column_1_2024_sales
```

### 6.3 Helper Dataframe

File: `helpers/dataframe.py`

Fungsinya:

- Membaca CSV dan Excel menjadi dataframe.
- Membersihkan nama kolom.
- Menebak tipe kolom MySQL dari tipe data pandas.
- Mengubah value pandas/numpy menjadi value Python standar sebelum dikirim ke MySQL.

### 6.4 Helper SQL Chat

File: `helpers/sql.py`

Fungsinya memvalidasi SQL dari model sebelum dijalankan:

- Hanya menerima satu statement.
- Menolak `ALTER`, `DROP`, `CREATE`, `TRUNCATE`, `REPLACE`, `GRANT`, `REVOKE`, `CALL`, `LOAD`, `OUTFILE`, dan `INFILE`.
- Mengizinkan operasi chat: `SELECT`, `WITH`, `INSERT`, `UPDATE`, `DELETE`.
- Mewajibkan `WHERE` untuk `UPDATE` dan `DELETE`.
- Menambahkan `LIMIT` otomatis untuk query baca jika belum ada.

### 6.5 Helper SQL Import

File: `helpers/sql_script.py`

Fungsinya:

- Membaca file `.sql`.
- Memecah script SQL menjadi statement terpisah.
- Mengabaikan komentar SQL.
- Melewati `USE` dan `CREATE DATABASE`.
- Melewati statement destruktif seperti `DROP`, `TRUNCATE`, `DELETE`, dan `UPDATE`.
- Mengubah `CREATE TABLE` menjadi `CREATE TABLE IF NOT EXISTS` jika opsi aktif.
- Mendukung `INSERT IGNORE` jika opsi aktif.
- Membaca `INSERT INTO table (columns) VALUES ...` untuk membuat tabel otomatis.

### 6.6 Repository MySQL

File: `repositories/mysql_repository.py`

Fungsinya menjadi satu pintu akses database:

- Membuka koneksi MySQL.
- Membuat database jika belum ada.
- Mengecek tabel dan kolom.
- Membuat tabel dari dataframe.
- Menambah kolom baru saat import.
- Insert dataframe secara batch.
- Mengambil schema database untuk prompt Ollama.
- Menjalankan SQL chat dengan validasi.
- Menjalankan import file SQL.

Bagian ini penting karena semua query database harus lewat repository, bukan langsung dari UI.

### 6.7 Service Ollama

File: `services/ollama_service.py`

Fungsinya:

- Mengirim prompt ke endpoint Ollama `/api/chat`.
- Meminta model menghasilkan JSON berisi `sql` dan `explanation`.
- Mem-parse response model.
- Membuat deskripsi hasil query dalam Bahasa Indonesia.
- Membuat deskripsi hasil operasi `INSERT`, `UPDATE`, atau `DELETE`.

Prompt system membatasi model agar hanya membuat SQL yang sesuai schema dan hanya memakai operasi yang diizinkan.

### 6.8 Service Chat

File: `services/chat_service.py`

Fungsinya menghubungkan pertanyaan user, schema database, Ollama, dan eksekusi SQL:

```text
ambil schema database
-> kirim pertanyaan + schema ke Ollama
-> terima SQL
-> validasi dan jalankan SQL
-> minta deskripsi hasil ke Ollama
-> kembalikan hasil ke UI
```

Jika proses deskripsi dari Ollama gagal, service membuat fallback description agar user tetap mendapat informasi hasil query.

### 6.9 Service Import

File: `services/import_service.py`

Fungsinya:

- Menyiapkan preview upload CSV/Excel.
- Menyiapkan preview upload SQL.
- Memanggil repository untuk membuat tabel/kolom.
- Memanggil repository untuk insert data.
- Mengembalikan jumlah baris yang berhasil diimport.

### 6.10 UI Sidebar

File: `ui/sidebar.py`

Fungsinya:

- Menyimpan konfigurasi ke `st.session_state`.
- Menampilkan ringkasan koneksi MySQL dan Ollama.
- Membuka dialog setting.
- Menyediakan tombol tes koneksi MySQL.
- Mengatur `max_rows` hasil query.

### 6.11 UI Chat

File: `ui/chat_view.py`

Fungsinya:

- Menampilkan history chat.
- Menerima pertanyaan user.
- Memanggil `ChatService`.
- Menampilkan deskripsi hasil, SQL yang dijalankan, dan dataframe hasil query.
- Menampilkan jumlah baris terdampak untuk `INSERT`, `UPDATE`, dan `DELETE`.

### 6.12 UI Import

File: `ui/import_view.py`

Fungsinya:

- Upload CSV, Excel, atau SQL.
- Preview data sebelum import.
- Menampilkan mapping nama kolom.
- Import data ke MySQL.
- Menampilkan opsi import SQL.

### 6.13 UI Schema

File: `ui/schema_view.py`

Fungsinya:

- Membaca daftar tabel database.
- Menampilkan ringkasan schema.
- Membantu user melihat tabel dan kolom yang tersedia sebelum bertanya di chat.

### 6.14 Entrypoint Streamlit

File: `app.py`

Fungsinya:

- Mengatur page config Streamlit.
- Memanggil sidebar.
- Membuat tab `Chat`, `Import`, `Schema`, dan `Testing`.
- Menghubungkan config dari sidebar ke masing-masing view.

## 7. Menyiapkan Database

Ada dua cara menyiapkan database.

### Cara A: Lewat MySQL Client

Buat database:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Import schema dan data awal:

```bash
mysql -u root -p chatbot < database/mysql.sql
```

Tambahkan data contoh lanjutan:

```bash
mysql -u root -p chatbot < database/data.sql
```

File `database/mysql.sql` membuat tabel:

- `users`
- `products`

File `database/data.sql` menambahkan data users dan products tambahan. Jalankan `database/mysql.sql` lebih dulu supaya foreign key dan id awal tersedia.

### Cara B: Lewat Tab Import Aplikasi

Jika belum ingin memakai command MySQL:

1. Jalankan aplikasi.
2. Buka sidebar, isi koneksi MySQL, aktifkan `Buat database jika belum ada`.
3. Buka tab `Import`.
4. Upload `database/mysql.sql`.
5. Klik `Import SQL ke MySQL`.
6. Upload `database/data.sql`.
7. Klik `Import SQL ke MySQL`.
8. Buka tab `Schema`, lalu klik `Refresh schema`.

## 8. Menjalankan Aplikasi

Aktifkan virtual environment:

```bash
source .venv/bin/activate
```

Jalankan Streamlit:

```bash
streamlit run app.py
```

Streamlit biasanya membuka browser otomatis. Jika tidak, buka URL yang muncul di terminal, umumnya:

```text
http://localhost:8501
```

## 9. Setting Aplikasi Pertama Kali

Di sidebar:

1. Klik `Buka Setting`.
2. Isi konfigurasi MySQL:
   - Host
   - Port
   - User
   - Password
   - Database
3. Aktifkan `Buat database jika belum ada` jika database belum dibuat.
4. Klik `Tes koneksi`.
5. Isi konfigurasi Ollama:
   - Endpoint, contoh `http://localhost:11434`
   - Model, contoh `qwen2.5:latest`
6. Atur `Maksimal baris hasil`.
7. Klik `Simpan`.

## 10. Cara Menggunakan

### Melihat Schema

1. Buka tab `Schema`.
2. Klik `Refresh schema`.
3. Pastikan tabel dan kolom muncul.

Contoh schema:

```text
users: id int, nama varchar(100), email varchar(100), password varchar(255), created_at timestamp
products: id int, user_id int, nama_product varchar(150), harga decimal(10,2), stok int, created_at timestamp
```

### Bertanya di Chat

Buka tab `Chat`, lalu coba pertanyaan:

```text
Tampilkan 10 user terbaru
```

```text
Produk apa saja yang stoknya kurang dari 10?
```

```text
Tampilkan nama user dan produk yang mereka miliki
```

```text
Tambahkan user bernama Dimas dengan email dimas@gmail.com dan password 123456
```

```text
Ubah stok Laptop Asus menjadi 9
```

```text
Hapus produk Mouse Logitech
```

Untuk operasi update dan delete, model harus menghasilkan SQL dengan `WHERE`. Jika tidak, aplikasi akan menolak query.

### Import CSV atau Excel

1. Buka tab `Import`.
2. Upload file `.csv`, `.xlsx`, atau `.xls`.
3. Isi nama tabel tujuan, contoh `customers`.
4. Cek preview dan mapping kolom.
5. Klik `Import ke MySQL`.
6. Buka tab `Schema`, klik `Refresh schema`.
7. Tanyakan data yang baru diimport dari tab `Chat`.

Saat import CSV/Excel:

- Nama kolom otomatis dinormalisasi.
- Jika tabel belum ada, tabel dibuat otomatis.
- Jika tabel sudah ada, kolom baru akan ditambahkan otomatis.
- Data dimasukkan ke MySQL secara batch.

### Import SQL

1. Buka tab `Import`.
2. Upload file `.sql`.
3. Cek preview SQL.
4. Pilih opsi import:
   - `Buat tabel otomatis jika INSERT mengarah ke tabel yang belum ada`
   - `Ubah CREATE TABLE menjadi CREATE TABLE IF NOT EXISTS`
   - `Abaikan data duplikat dengan INSERT IGNORE`
5. Klik `Import SQL ke MySQL`.

## 11. Keamanan Query

Aplikasi memiliki beberapa perlindungan:

- Chat hanya menerima satu statement SQL.
- Chat menolak query struktur database seperti `DROP`, `ALTER`, dan `CREATE`.
- Chat menolak `UPDATE` atau `DELETE` tanpa `WHERE`.
- Query baca otomatis dibatasi dengan `LIMIT`.
- Import SQL melewati statement destruktif.
- Query dinamis untuk tabel/kolom memakai backtick.

Tetap disarankan memakai database testing saat mencoba fitur write seperti `INSERT`, `UPDATE`, dan `DELETE`.

## 12. Troubleshooting

### MySQL gagal terkoneksi

Cek:

- Host dan port benar.
- User dan password benar.
- Database server sedang menyala.
- IP komputer aplikasi diizinkan jika memakai database cloud.
- Port MySQL tidak diblokir firewall.

Tes manual:

```bash
mysql -h localhost -P 3306 -u root -p
```

### Database tidak ditemukan

Solusi:

- Aktifkan `Buat database jika belum ada` di sidebar.
- Atau buat manual:

```bash
mysql -u root -p -e "CREATE DATABASE chatbot;"
```

### Ollama gagal

Cek:

- Ollama server sedang berjalan.
- Endpoint benar.
- Model sudah tersedia.
- Komputer aplikasi bisa mengakses endpoint.

Tes:

```bash
curl http://localhost:11434/api/tags
```

Jika model belum ada:

```bash
ollama pull qwen2.5:latest
```

### Model membuat SQL yang ditolak

Penyebab umum:

- Pertanyaan meminta tabel atau kolom yang tidak ada.
- Schema belum di-refresh atau database masih kosong.
- Model membuat `UPDATE` atau `DELETE` tanpa `WHERE`.
- Model membuat statement yang tidak didukung.

Solusi:

- Buka tab `Schema`, klik `Refresh schema`.
- Buat pertanyaan lebih spesifik.
- Sebutkan nama tabel atau kolom yang benar.

### Import CSV gagal

Cek:

- File benar-benar CSV.
- Delimiter file konsisten.
- Encoding file valid.
- Header kolom tidak kosong semua.

Jika CSV memakai format aneh, buka di spreadsheet lalu export ulang sebagai CSV UTF-8.

### Import SQL gagal

Cek:

- Jalankan `database/mysql.sql` sebelum `database/data.sql`.
- Pastikan foreign key mengarah ke data yang sudah ada.
- Hindari dump SQL yang bergantung pada procedure, trigger, atau fitur MySQL lanjutan.
- Jika ada data duplikat, aktifkan opsi `INSERT IGNORE`.

## 13. Checklist Sampai Bisa Digunakan

Gunakan checklist ini saat setup:

- Python virtual environment sudah dibuat.
- Dependency dari `requirements.txt` sudah terinstall.
- MySQL server sudah berjalan.
- Database `chatbot` tersedia atau opsi auto-create aktif.
- Ollama server bisa diakses.
- Model `qwen2.5:latest` tersedia atau model lain sudah diisi di setting.
- Aplikasi berhasil dijalankan dengan `streamlit run app.py`.
- Tes koneksi MySQL berhasil dari sidebar.
- Schema bisa di-refresh.
- Data sample berhasil diimport.
- Pertanyaan chat pertama berhasil menghasilkan SQL dan dataframe.

## 14. Catatan Pengembangan Lanjutan

Beberapa pengembangan yang bisa ditambahkan:

- Menambahkan file `.env` dengan `python-dotenv`.
- Membuat halaman login.
- Membatasi operasi write hanya untuk role tertentu.
- Menambahkan konfirmasi sebelum `INSERT`, `UPDATE`, dan `DELETE`.
- Menyimpan history chat ke database.
- Menambahkan unit test untuk helper SQL dan parser import.
- Menambahkan Docker Compose untuk MySQL dan aplikasi.

## 15. Source Code Lengkap

Bagian ini berisi source code final yang bisa disalin ke file sesuai path masing-masing. Untuk `config.py`, sesuaikan host, port, user, database, URL Ollama, dan model dengan environment yang dipakai.

### requirements.txt

```text
streamlit>=1.35
mysql-connector-python>=8.4
pandas>=2.2
requests>=2.32
urllib3<2
openpyxl>=3.1
```

### config.py

```python
DEFAULT_OLLAMA_MODEL = "qwen2.5:latest"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

DEFAULT_MYSQL_DATABASE = "chatbot"
DEFAULT_MYSQL_HOST = "localhost"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "root"
```

### app.py

```python
import streamlit as st

from ui.chat_view import render_chat
from ui.import_view import render_import
from ui.schema_view import render_schema
from ui.sidebar import render_sidebar


def main() -> None:
    st.set_page_config(page_title="Chatbot MySQL Ollama", layout="wide")
    st.title("Chatbot MySQL Ollama")

    mysql_config, ollama_url, model, max_rows = render_sidebar()

    chat_tab, import_tab, schema_tab, testing = st.tabs(["Chat", "Import", "Schema", "Testing"])
    with chat_tab:
        render_chat(mysql_config, ollama_url, model, max_rows)
    with import_tab:
        render_import(mysql_config)
    with schema_tab:
        render_schema(mysql_config)
    with testing:
        st.info("Fitur testing masih dalam pengembangan. Nantikan update selanjutnya!")

if __name__ == "__main__":
    main()
```

### helpers/env.py

```python
import os


def env_int(name: str, default: int) -> int:
    """Membaca environment variable bertipe integer dengan nilai fallback."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        # Jika env kosong atau bukan angka, aplikasi tetap jalan memakai default.
        return default
```

### helpers/identifiers.py

```python
import re
from typing import Any, Iterable, List


def quote_identifier(identifier: str) -> str:
    """Membungkus nama tabel/kolom dengan backtick MySQL."""
    # Backtick di dalam nama juga di-escape agar tetap aman untuk query dinamis.
    return "`" + identifier.replace("`", "``") + "`"


def normalize_identifier(value: Any, fallback: str) -> str:
    """Mengubah nama kolom/tabel dari file upload menjadi identifier MySQL yang aman."""
    # Nama dibuat lowercase dan spasi/simbol diganti underscore.
    name = str(value or "").strip().lower()
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    # Jika nama kosong atau diawali angka, pakai fallback agar valid sebagai nama kolom/tabel.
    if not name:
        name = fallback
    if name[0].isdigit():
        name = f"{fallback}_{name}"

    # MySQL membatasi panjang identifier maksimal 64 karakter.
    return name[:64]


def make_unique(names: Iterable[str]) -> List[str]:
    """Membuat daftar nama menjadi unik tanpa mengubah urutan aslinya."""
    seen = {}
    result = []

    for raw_name in names:
        # Batasi sejak awal supaya suffix tambahan tidak melewati limit MySQL.
        name = raw_name[:64]
        base = name[:58]
        count = seen.get(name, 0)

        # Jika nama sudah ada, tambahkan suffix angka: nama, nama_2, nama_3.
        if count:
            candidate = f"{base}_{count + 1}"[:64]
            while candidate in seen:
                count += 1
                candidate = f"{base}_{count + 1}"[:64]
            name = candidate

        seen[name] = seen.get(name, 0) + 1
        result.append(name)

    return result
```

### helpers/dataframe.py

```python
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
```

### helpers/sql.py

```python
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
```

### helpers/sql_script.py

```python
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
```

### repositories/mysql_repository.py

```python
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
```

### services/ollama_service.py

```python
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
```

### services/chat_service.py

```python
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
```

### services/import_service.py

```python
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
```

### ui/sidebar.py

```python
import os
from typing import Any, Dict, Tuple

import requests
import streamlit as st

from config import (
    DEFAULT_MYSQL_DATABASE,
    DEFAULT_MYSQL_HOST,
    DEFAULT_MYSQL_PORT,
    DEFAULT_MYSQL_USER,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
)
from helpers.env import env_int
from repositories.mysql_repository import MySqlRepository


MYSQL_SETTING_KEYS = {
    "mysql_host": "setting_mysql_host",
    "mysql_port": "setting_mysql_port",
    "mysql_user": "setting_mysql_user",
    "mysql_password": "setting_mysql_password",
    "mysql_database": "setting_mysql_database",
    "create_database": "setting_create_database",
}
OLLAMA_SETTING_KEYS = {
    "ollama_host": "setting_ollama_host",
    "ollama_model": "setting_ollama_model",
    "max_rows": "setting_max_rows",
}
SETTING_KEYS = MYSQL_SETTING_KEYS | OLLAMA_SETTING_KEYS


def init_session_state() -> None:
    st.session_state.setdefault("mysql_host", os.getenv("MYSQL_HOST", DEFAULT_MYSQL_HOST))
    st.session_state.setdefault("mysql_port", env_int("MYSQL_PORT", DEFAULT_MYSQL_PORT))
    st.session_state.setdefault("mysql_user", os.getenv("MYSQL_USER", DEFAULT_MYSQL_USER))
    st.session_state.setdefault("mysql_password", os.getenv("MYSQL_PASSWORD", ""))
    st.session_state.setdefault("mysql_database", os.getenv("MYSQL_DATABASE", DEFAULT_MYSQL_DATABASE))
    st.session_state.setdefault("create_database", True)

    st.session_state.setdefault("ollama_host", os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL))
    st.session_state.setdefault("ollama_model", os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))
    st.session_state.setdefault("max_rows", 100)

    for active_key, draft_key in SETTING_KEYS.items():
        st.session_state.setdefault(draft_key, st.session_state[active_key])


def get_mysql_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.mysql_host,
        "port": int(st.session_state.mysql_port),
        "user": st.session_state.mysql_user,
        "password": st.session_state.mysql_password,
        "database": st.session_state.mysql_database,
        "create_database": st.session_state.create_database,
    }


def get_mysql_draft_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.setting_mysql_host,
        "port": int(st.session_state.setting_mysql_port),
        "user": st.session_state.setting_mysql_user,
        "password": st.session_state.setting_mysql_password,
        "database": st.session_state.setting_mysql_database,
        "create_database": st.session_state.setting_create_database,
    }


def get_ollama_draft_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.setting_ollama_host,
        "model": st.session_state.setting_ollama_model,
    }


def sync_active_to_draft() -> None:
    for active_key, draft_key in SETTING_KEYS.items():
        st.session_state[draft_key] = st.session_state[active_key]


def save_draft_settings() -> None:
    old_mysql_config = get_mysql_config()

    for active_key, draft_key in SETTING_KEYS.items():
        st.session_state[active_key] = st.session_state[draft_key]

    if old_mysql_config != get_mysql_config():
        st.session_state.messages = []
        st.session_state.schema_tables = None
        st.session_state.schema_text = None


def test_ollama_connection(base_url: str, model: str) -> Tuple[bool, str]:
    response = requests.get(base_url.rstrip("/") + "/api/tags", timeout=15)
    response.raise_for_status()

    models = response.json().get("models", [])
    model_names = {item.get("name") for item in models if item.get("name")}

    if model in model_names:
        return True, f"Ollama terhubung dan model `{model}` tersedia."

    available = ", ".join(sorted(model_names)[:5]) or "tidak ada model"
    return (
        False,
        f"Ollama terhubung, tetapi model `{model}` belum ditemukan. Model tersedia: {available}.",
    )


@st.dialog("Setting MYSQL & Ollama")
def show_dialog() -> None:
    st.header("MySQL")

    st.text_input(
        "Host MySQL",
        key="setting_mysql_host",
    )

    st.number_input(
        "Port MySQL",
        min_value=1,
        max_value=65535,
        key="setting_mysql_port",
    )

    st.text_input(
        "User MySQL",
        key="setting_mysql_user",
    )

    st.text_input(
        "Password MySQL",
        type="password",
        key="setting_mysql_password",
    )

    st.text_input(
        "Database",
        key="setting_mysql_database",
    )

    st.checkbox(
        "Buat database jika belum ada",
        key="setting_create_database",
    )

    if st.button("Tes MySQL", use_container_width=True):
        try:
            connection = MySqlRepository(get_mysql_draft_config()).connect()
            connection.close()
            st.success("MySQL terhubung.")
        except Exception as exc:
            st.error(f"MySQL gagal: {exc}")

    st.divider()
    st.header("Ollama")

    st.text_input(
        "Endpoint",
        key="setting_ollama_host",
    )
    st.text_input(
        "Model",
        key="setting_ollama_model",
    )

    if st.button("Tes Ollama", use_container_width=True):
        try:
            ollama_config = get_ollama_draft_config()
            found, message = test_ollama_connection(
                ollama_config["host"],
                ollama_config["model"],
            )
            if found:
                st.success(message)
            else:
                st.warning(message)
        except Exception as exc:
            st.error(f"Ollama gagal: {exc}")

    st.slider(
        "Maksimal baris hasil",
        min_value=10,
        max_value=1000,
        key="setting_max_rows",
    )

    if st.button("Simpan", type="primary", use_container_width=True):
        save_draft_settings()
        st.rerun()


def render_sidebar() -> Tuple[Dict[str, Any], str, str, int]:
    init_session_state()

    with st.sidebar:
        st.header("Koneksi")

        st.write("MySQL")
        st.write(
            f"User: { st.session_state.mysql_user}"
        )
        st.caption(
            f"Host: {st.session_state.mysql_host}"
        )
        st.caption(
            f"Port: {st.session_state.mysql_port}"
        )
        st.caption(
            f"Database: {st.session_state.mysql_database}"
        )

        st.write("Ollama")
        st.caption(
            f"Model: {st.session_state.ollama_model}"
        )
        st.caption(
            f"Endpoint: {st.session_state.ollama_host}"
        )

        if st.button("Buka Setting", use_container_width=True):
            sync_active_to_draft()
            show_dialog()

    return (
        get_mysql_config(),
        st.session_state.ollama_host,
        st.session_state.ollama_model,
        st.session_state.max_rows,
    )
```

### ui/chat_view.py

```python
import html
from typing import Dict

import pandas as pd
import streamlit as st

from repositories.mysql_repository import MySqlRepository
from services.chat_service import ChatService
from services.ollama_service import OllamaService


SUGGESTED_PROMPTS = [
    "Tampilkan 10 data user terbaru",
    "Produk apa saja yang stoknya kurang dari 10?",
    "Tampilkan nama user dan produk yang mereka miliki",
    "Hitung total produk berdasarkan user",
]


def apply_chat_styles() -> None:
    st.markdown(
        """
        <style>
            .chat-topbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.6rem 0 1.2rem;
                border-bottom: 1px solid rgba(49, 51, 63, 0.12);
                margin-bottom: 1.4rem;
            }

            .chat-title {
                margin: 0;
                font-size: 1.45rem;
                font-weight: 650;
                letter-spacing: 0;
            }

            .chat-meta {
                margin-top: 0.15rem;
                color: rgba(49, 51, 63, 0.68);
                font-size: 0.88rem;
            }

            .chat-hero {
                min-height: 48vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 2rem 0.5rem;
            }

            .chat-hero h2 {
                font-size: clamp(1.8rem, 3vw, 2.6rem);
                line-height: 1.15;
                margin: 0 0 0.6rem;
                font-weight: 700;
                letter-spacing: 0;
            }

            .chat-hero p {
                margin: 0;
                max-width: 620px;
                color: rgba(49, 51, 63, 0.68);
                font-size: 1rem;
                line-height: 1.6;
            }

            .message-card {
                width: fit-content;
                max-width: min(760px, 100%);
                border-radius: 1.1rem;
                padding: 0.82rem 1rem;
                line-height: 1.6;
                border: 1px solid rgba(49, 51, 63, 0.10);
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
                overflow-wrap: anywhere;
            }

            .chat-row {
                display: flex;
                width: 100%;
                margin: 0.65rem 0;
            }

            .chat-row.user {
                justify-content: flex-end;
            }

            .chat-row.assistant {
                justify-content: flex-start;
            }

            .message-card.user {
                background: #2C3947;
            }

            .message-card.assistant {
                background: #2C3947;
            }

            .message-label {
                margin: 1rem 0 0.4rem;
                color: rgba(49, 51, 63, 0.68);
                font-size: 0.82rem;
                font-weight: 650;
                text-transform: uppercase;
            }

            div[data-testid="stChatInput"] {
                max-width: 980px;
                margin: 0 auto;
            }

            @media (max-width: 640px) {
                .chat-topbar {
                    align-items: flex-start;
                    flex-direction: column;
                }

                .chat-hero {
                    min-height: 42vh;
                    padding-top: 1rem;
                }

                .message-card {
                    max-width: 100%;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_chat_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_chat_question", None)


def render_header(model: str, max_rows: int) -> None:
    left, right = st.columns([1, 0.22])
    with left:
        st.markdown(
            f"""
            <div class="chat-topbar">
                <div>
                    <p class="chat-title">Chat Database</p>
                    <div class="chat-meta">Model: {html.escape(model)} - Maksimal {max_rows} baris</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Reset", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_chat_question = None
            st.rerun()


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="chat-hero">
            <h2>Ada yang bisa saya bantu?</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(2)
    for index, prompt in enumerate(SUGGESTED_PROMPTS):
        with columns[index % 2]:
            if st.button(prompt, key=f"suggested_prompt_{index}", use_container_width=True):
                st.session_state.pending_chat_question = prompt
                st.rerun()


def render_text_bubble(content: str, role: str) -> None:
    safe_content = html.escape(str(content)).replace("\n", "<br>")
    st.markdown(
        (
            f'<div class="chat-row {role}">'
            f'<div class="message-card {role}">{safe_content}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_message(message: Dict) -> None:
    role = message["role"]

    render_text_bubble(message["content"], role)

    if message.get("sql"):
        st.markdown('<div class="message-label">SQL</div>', unsafe_allow_html=True)
        st.code(message["sql"], language="sql")

    dataframe = message.get("dataframe")
    if isinstance(dataframe, pd.DataFrame):
        st.markdown('<div class="message-label">Hasil</div>', unsafe_allow_html=True)
        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )
    elif message.get("operation") in {"insert", "update", "delete"}:
        st.info(
            f"Operasi {message['operation'].upper()} selesai. "
            f"{message.get('affected_rows', 0)} baris terdampak."
        )


def create_assistant_message(
    question: str,
    mysql_config,
    ollama_url: str,
    model: str,
    max_rows: int,
) -> Dict:
    service = ChatService(
        MySqlRepository(mysql_config),
        OllamaService(ollama_url, model),
    )

    with st.spinner("Membaca database..."):
        result = service.ask(question, max_rows)

    return {
        "affected_rows": result.affected_rows,
        "role": "assistant",
        "content": result.explanation,
        "operation": result.operation,
        "sql": result.sql,
        "dataframe": result.dataframe,
    }


def handle_question(
    question: str,
    mysql_config,
    ollama_url: str,
    model: str,
    max_rows: int,
) -> None:
    user_message = {"role": "user", "content": question}
    st.session_state.messages.append(user_message)
    render_message(user_message)

    try:
        assistant_message = create_assistant_message(
            question,
            mysql_config,
            ollama_url,
            model,
            max_rows,
        )
        st.session_state.messages.append(assistant_message)
        render_message(assistant_message)
    except Exception as exc:
        error_message = f"Gagal membuat atau menjalankan query: {exc}"
        assistant_message = {"role": "assistant", "content": error_message}
        st.session_state.messages.append(assistant_message)
        render_message(assistant_message)

    st.rerun()


def render_chat(mysql_config, ollama_url: str, model: str, max_rows: int) -> None:
    apply_chat_styles()
    init_chat_state()

    render_header(model, max_rows)
    pending_question = st.session_state.pending_chat_question
    st.session_state.pending_chat_question = None

    if not st.session_state.messages:
        if not pending_question:
            render_empty_state()
    else:
        for message in st.session_state.messages:
            render_message(message)

    typed_question = st.chat_input("Kirim pesan ke database")
    question = pending_question or typed_question

    if question:
        handle_question(question, mysql_config, ollama_url, model, max_rows)
```

### ui/import_view.py

```python
import pandas as pd
import streamlit as st

from repositories.mysql_repository import MySqlRepository
from services.import_service import ImportService


def render_import(mysql_config) -> None:
    st.subheader("Import Data")
    uploaded_file = st.file_uploader(
        "File CSV, Excel, atau SQL",
        type=["csv", "xlsx", "xls", "sql"],
    )

    if uploaded_file is None:
        return

    service = ImportService(MySqlRepository(mysql_config))

    if uploaded_file.name.lower().endswith(".sql"):
        render_sql_import(service, uploaded_file)
        return

    raw_table_name = st.text_input("Nama tabel tujuan", value="import_data")

    try:
        preview = service.prepare_upload(uploaded_file, raw_table_name)
    except Exception as exc:
        st.error(f"File gagal dibaca: {exc}")
        return

    st.caption(f"Tabel tujuan: `{preview.table_name}`")
    with st.expander("Mapping kolom"):
        mapping_df = pd.DataFrame(
            [
                {"kolom_file": key, "kolom_mysql": value}
                for key, value in preview.column_mapping.items()
            ]
        )
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)

    st.dataframe(preview.dataframe.head(50), use_container_width=True)

    if st.button("Import ke MySQL", type="primary", use_container_width=True):
        try:
            result = service.import_preview(preview)
            status = "Tabel dibuat" if result.created_table else "Tabel sudah ada"

            if result.created_columns:
                st.success(
                    f"{status}. {len(result.created_columns)} kolom baru siap. "
                    f"{result.inserted} baris berhasil diinsert."
                )
            else:
                st.success(f"{status}. {result.inserted} baris berhasil diinsert.")
        except Exception as exc:
            st.error(f"Import gagal: {exc}")


def render_sql_import(service: ImportService, uploaded_file) -> None:
    try:
        preview = service.prepare_sql_upload(uploaded_file)
    except Exception as exc:
        st.error(f"File SQL gagal dibaca: {exc}")
        return

    st.caption(f"File SQL: `{preview.file_name}`")
    st.info(f"Terdeteksi {len(preview.statements)} statement SQL.")

    auto_create_tables = st.checkbox(
        "Buat tabel otomatis jika INSERT mengarah ke tabel yang belum ada",
        value=True,
    )
    create_table_if_not_exists = st.checkbox(
        "Ubah CREATE TABLE menjadi CREATE TABLE IF NOT EXISTS",
        value=True,
    )
    insert_ignore = st.checkbox(
        "Abaikan data duplikat dengan INSERT IGNORE",
        value=False,
    )

    with st.expander("Preview SQL"):
        st.code(preview.script[:8000], language="sql")
        if len(preview.script) > 8000:
            st.caption("Preview dipotong sampai 8000 karakter.")

    if st.button("Import SQL ke MySQL", type="primary", use_container_width=True):
        try:
            result = service.import_sql_preview(
                preview,
                auto_create_tables=auto_create_tables,
                create_table_if_not_exists=create_table_if_not_exists,
                insert_ignore=insert_ignore,
            )

            if result.created_tables:
                st.success(
                    "Tabel otomatis dibuat: "
                    + ", ".join(f"`{table}`" for table in result.created_tables)
                )
            if result.created_columns:
                with st.expander("Kolom otomatis dibuat"):
                    for table, columns in result.created_columns.items():
                        st.write(f"- `{table}`: " + ", ".join(f"`{column}`" for column in columns))

            if result.skipped_reasons:
                st.warning(
                    f"{len(result.skipped_reasons)} statement dilewati. "
                    f"{result.executed} statement berhasil dijalankan."
                )
                with st.expander("Statement yang dilewati"):
                    for reason in result.skipped_reasons:
                        st.write(f"- {reason}")
            else:
                st.success(f"{result.executed} statement SQL berhasil dijalankan.")
        except Exception as exc:
            st.error(f"Import SQL gagal: {exc}")
```

### ui/schema_view.py

```python
import streamlit as st

from repositories.mysql_repository import MySqlRepository


def render_schema(mysql_config) -> None:
    st.subheader("Schema")

    if st.button("Refresh schema", use_container_width=True):
        repository = MySqlRepository(mysql_config)
        try:
            connection = repository.connect()
            try:
                st.session_state.schema_tables = repository.list_tables(connection)
                st.session_state.schema_text = repository.get_schema_summary(connection)
            finally:
                connection.close()
        except Exception as exc:
            st.error(f"Schema gagal dibaca: {exc}")
            return

    tables = st.session_state.get("schema_tables")
    schema = st.session_state.get("schema_text")

    if tables is None:
        st.info("Klik refresh untuk membaca schema.")
        return

    if not tables:
        st.info("Belum ada tabel.")
        return

    st.code(schema, language="text")
```

### database/mysql.sql

```sql
-- =====================================
-- TABEL USERS
-- =====================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- TABEL PRODUCTS
-- Relasi ke users
-- =====================================
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    nama_product VARCHAR(150) NOT NULL,
    harga DECIMAL(10,2) NOT NULL,
    stok INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_user
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- =====================================
-- DATA USERS
-- =====================================
INSERT INTO users (nama, email, password) VALUES
('Fajar Setiawan', 'fajar@gmail.com', '123456'),
('Budi Santoso', 'budi@gmail.com', '123456'),
('Siti Aminah', 'siti@gmail.com', '123456');

-- =====================================
-- DATA PRODUCTS
-- user_id relasi ke users.id
-- =====================================
INSERT INTO products (user_id, nama_product, harga, stok) VALUES
(1, 'Laptop Asus', 8500000, 10),
(1, 'Mouse Logitech', 250000, 25),
(2, 'Keyboard Mechanical', 750000, 15),
(2, 'Monitor LG 24 Inch', 2200000, 8),
(3, 'Headset Gaming', 450000, 20);
```

### database/data.sql

```sql
-- =====================================
-- INSERT DATA USERS (20 DATA)
-- =====================================
INSERT INTO users (nama, email, password) VALUES
('Andi Wijaya', 'andi@gmail.com', '123456'),
('Rina Marlina', 'rina@gmail.com', '123456'),
('Dewi Lestari', 'dewi@gmail.com', '123456'),
('Agus Saputra', 'agus@gmail.com', '123456'),
('Joko Prasetyo', 'joko@gmail.com', '123456'),
('Lina Kartika', 'lina@gmail.com', '123456'),
('Rahmat Hidayat', 'rahmat@gmail.com', '123456'),
('Yuni Astuti', 'yuni@gmail.com', '123456'),
('Dian Permata', 'dian@gmail.com', '123456'),
('Rudi Hartono', 'rudi@gmail.com', '123456'),
('Tono Sapri', 'tono@gmail.com', '123456'),
('Nina Sari', 'nina@gmail.com', '123456'),
('Arif Nugroho', 'arif@gmail.com', '123456'),
('Putri Ayu', 'putri@gmail.com', '123456'),
('Hendra Gunawan', 'hendra@gmail.com', '123456'),
('Maya Fitri', 'maya@gmail.com', '123456'),
('Ilham Ramadhan', 'ilham@gmail.com', '123456');

-- =====================================
-- INSERT DATA PRODUCTS (50 DATA)
-- =====================================
INSERT INTO products (user_id, nama_product, harga, stok) VALUES
(1, 'Laptop Asus ROG', 15000000, 5),
(1, 'Mouse Logitech G102', 250000, 20),
(1, 'Keyboard Rexus', 450000, 15),

(2, 'Monitor Samsung 24"', 2200000, 10),
(2, 'SSD Samsung 1TB', 1800000, 12),
(2, 'Flashdisk Sandisk 64GB', 120000, 50),

(3, 'Headset Gaming Fantech', 350000, 25),
(3, 'Webcam Logitech C270', 400000, 10),
(3, 'Mousepad RGB', 150000, 30),

(4, 'Printer Epson L3210', 2500000, 8),
(4, 'Tinta Printer Epson', 85000, 40),

(5, 'Kursi Gaming', 1750000, 7),
(5, 'Meja Komputer', 950000, 10),

(6, 'Router TP-Link', 450000, 18),
(6, 'Kabel LAN 10M', 75000, 100),

(7, 'Smartphone Samsung A54', 5200000, 9),
(7, 'Case HP Samsung', 85000, 25),
(7, 'Tempered Glass', 35000, 60),

(8, 'iPhone 13', 12500000, 4),
(8, 'Charger iPhone', 350000, 20),

(9, 'Powerbank Xiaomi 20000mAh', 275000, 15),
(9, 'Kabel USB Type-C', 45000, 80),

(10, 'Speaker Bluetooth JBL', 650000, 13),
(10, 'Microphone Gaming', 550000, 9),

(11, 'TV LG 43 Inch', 4800000, 6),
(11, 'Remote TV Universal', 65000, 30),

(12, 'Laptop Acer Nitro 5', 13500000, 5),
(12, 'Cooling Pad Laptop', 120000, 22),

(13, 'Drone DJI Mini', 7500000, 3),
(13, 'Baterai Drone', 850000, 10),

(14, 'Kamera Canon EOS', 9500000, 4),
(14, 'Tripod Kamera', 250000, 16),

(15, 'Jam Smartwatch Xiaomi', 550000, 14),
(15, 'Strap Smartwatch', 50000, 35),

(16, 'Playstation 5', 9500000, 2),
(16, 'Stick PS5', 1200000, 11),
(16, 'Game FIFA 25', 850000, 17),

(17, 'Nintendo Switch', 5200000, 6),
(17, 'Game Zelda', 950000, 10),

(18, 'Harddisk External 2TB', 1250000, 12),
(18, 'USB Hub 4 Port', 95000, 25),

(19, 'Tablet iPad Air', 9800000, 5),
(19, 'Apple Pencil', 1750000, 7),

(20, 'Smart TV Xiaomi', 4200000, 6),
(20, 'Bracket TV', 150000, 18),

(5, 'Lampu LED RGB', 95000, 40),
(6, 'Keyboard Mechanical RGB', 850000, 14),
(7, 'Mouse Wireless', 175000, 28),
(8, 'Laptop Stand Aluminium', 225000, 19),
(9, 'Headphone Sony', 1450000, 9),
(10, 'Action Camera', 3200000, 5),
(11, 'Ring Light', 275000, 13),
(12, 'Gaming Desk', 2100000, 4),
(13, 'PC Rakitan Gaming', 18500000, 2),
(14, 'RAM DDR4 16GB', 950000, 21),
(15, 'VGA RTX 4070', 12500000, 3);

-- =====================================
-- MENAMPILKAN DATA RELASI USER & PRODUCT
-- =====================================
```
