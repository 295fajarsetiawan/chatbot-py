import os


def env_int(name: str, default: int) -> int:
    """Membaca environment variable bertipe integer dengan nilai fallback."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        # Jika env kosong atau bukan angka, aplikasi tetap jalan memakai default.
        return default
