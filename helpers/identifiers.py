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
