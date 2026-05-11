from __future__ import annotations

import random
import re
from datetime import datetime
from zoneinfo import ZoneInfo


GREETINGS = {
    "halo",
    "hai",
    "hei",
    "hello",
    "hi",
    "pagi",
    "siang",
    "sore",
    "malam",
    "assalamualaikum",
}

HELP_RESPONSES = [
    "Saya bisa bantu jawab pertanyaan umum, membuat ide project, menjelaskan Python, atau menemani brainstorming.",
    "Coba tanya tentang Python, website, data, atau minta saya buatkan contoh langkah kerja.",
    "Saya siap bantu. Kirim topik yang ingin kamu bahas, nanti saya jawab singkat dan jelas.",
]

THANKS_RESPONSES = [
    "Sama-sama. Senang bisa bantu.",
    "Dengan senang hati.",
    "Sip, kalau ada yang mau dilanjutkan tinggal kirim lagi.",
]

KEYWORD_RESPONSES = [
    (
        ("python", "flask"),
        "Flask cocok untuk website Python kecil sampai menengah. Di project ini Flask menangani halaman utama dan endpoint chat.",
    ),
    (
        ("html", "css", "javascript"),
        "HTML membentuk struktur halaman, CSS mengatur tampilan, dan JavaScript mengirim pesan ke backend Flask.",
    ),
    (
        ("website", "web", "situs"),
        "Website ini memakai Flask sebagai backend dan halaman chat interaktif di browser.",
    ),
    (
        ("machine learning", "ml", "model", "prediksi"),
        "Untuk menambah machine learning, kamu bisa load model di backend lalu panggil dari endpoint chat.",
    ),
    (
        ("harga", "mobil"),
        "Kalau ingin chatbot harga mobil, kita bisa hubungkan bot ini ke model prediksi harga dari file training kamu.",
    ),
    (
        ("diabetes", "kesehatan"),
        "Kalau ingin chatbot kesehatan, gunakan jawaban yang hati-hati dan beri catatan bahwa pengguna perlu konsultasi dokter.",
    ),
]

FALLBACKS = [
    "Menarik. Bisa ceritakan sedikit lebih detail?",
    "Saya menangkap arahnya, tapi butuh konteks tambahan supaya jawabannya tepat.",
    "Boleh. Mau saya bantu dari sisi konsep, kode, atau langkah pengerjaannya?",
    "Saya bisa bantu susun jawaban atau contoh kodenya. Bagian mana yang ingin difokuskan?",
]

MONTH_NAMES_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def current_jakarta_time() -> str:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    return f"{now:%H:%M}, {now.day:02d} {MONTH_NAMES_ID[now.month]} {now.year}"


def has_any(text: str, words: tuple[str, ...] | set[str]) -> bool:
    return any(word in text for word in words)


def generate_reply(message: str) -> str:
    text = normalize(message)

    if any(re.search(rf"\b{re.escape(word)}\b", text) for word in GREETINGS):
        return "Halo. Saya ChatBot Python, siap bantu kamu."

    if has_any(text, ("terima kasih", "makasih", "thanks", "thank you")):
        return random.choice(THANKS_RESPONSES)

    if has_any(text, ("bantuan", "help", "bisa apa", "fitur")):
        return random.choice(HELP_RESPONSES)

    if has_any(text, ("nama kamu", "siapa kamu", "kamu siapa")):
        return "Saya ChatBot Python, asisten sederhana yang berjalan dari website Flask."

    if has_any(text, ("jam berapa", "tanggal", "hari ini", "waktu")):
        return f"Waktu Jakarta sekarang sekitar {current_jakarta_time()}."

    for keywords, reply in KEYWORD_RESPONSES:
        if has_any(text, keywords):
            return reply

    if text.endswith("?"):
        return "Pertanyaan bagus. Saya butuh sedikit konteks lagi supaya bisa menjawab lebih tepat."

    return random.choice(FALLBACKS)
