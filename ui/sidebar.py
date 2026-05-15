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
