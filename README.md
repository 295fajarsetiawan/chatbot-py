# ChatBot Python Website

Project website chatbot sederhana dengan Python Flask. Bot berjalan lokal dengan jawaban rule-based, jadi bisa dicoba tanpa API key.

## Struktur

```text
.
├── app.py
├── bot.py
├── requirements.txt
├── static
│   ├── app.js
│   └── style.css
└── templates
    └── index.html
```

## Cara menjalankan

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Buka browser ke:

```text
http://127.0.0.1:5000
```

## Mengembangkan jawaban bot

Edit file `bot.py`, terutama bagian `KEYWORD_RESPONSES`, `HELP_RESPONSES`, dan `FALLBACKS`.
