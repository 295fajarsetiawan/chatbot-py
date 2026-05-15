# Chatbot MySQL Ollama

Aplikasi Streamlit untuk chat query ke database MySQL memakai Ollama.

## Dokumentasi

- [Tutorial membuat project dari awal sampai bisa digunakan](docs/tutorial-membuat-project.md)

## Fitur

- Chat natural language ke database MySQL.
- Chat bisa menjalankan `SELECT`, `INSERT`, `UPDATE`, dan `DELETE`.
- `UPDATE` dan `DELETE` dari chat wajib memiliki `WHERE`.
- AI memakai endpoint Ollama `http://peradiprof.or.id:11434`.
- Import CSV, Excel, atau SQL ke MySQL.
- Jika tabel belum ada, aplikasi membuat tabel dan kolom.
- Jika tabel sudah ada, aplikasi menambah kolom yang belum ada lalu insert data.
- Import SQL mendukung `CREATE TABLE` dan `INSERT`.
- Import SQL yang hanya berisi `INSERT` juga bisa membuat tabel otomatis dari daftar kolom.

## Struktur Folder

```text
.
├── app.py
├── config.py
├── helpers/
│   ├── dataframe.py
│   ├── env.py
│   ├── identifiers.py
│   ├── sql_script.py
│   └── sql.py
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

- `app.py`: entrypoint Streamlit.
- `helpers`: fungsi kecil yang reusable.
- `repositories`: akses database MySQL.
- `services`: logic import, chat, dan request ke Ollama.
- `ui`: tampilan Streamlit per halaman/tab.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Jalankan

```bash
streamlit run app.py
```

Default endpoint Ollama bisa diubah dari sidebar atau environment:

```bash
export OLLAMA_BASE_URL=http://peradiprof.or.id:11434
export OLLAMA_MODEL=llama3.1
```

Konfigurasi MySQL juga bisa diisi dari sidebar atau environment:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=chatbot
```
