import os
from typing import Any, Dict, Tuple

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


def get_mysql_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.mysql_host,
        "port": int(st.session_state.mysql_port),
        "user": st.session_state.mysql_user,
        "password": st.session_state.mysql_password,
        "database": st.session_state.mysql_database,
        "create_database": st.session_state.create_database,
    }


def render_sidebar() -> Tuple[Dict[str, Any], str, str, int]:
    with st.sidebar:
        st.header("Koneksi")
        st.text_input(
            "Host MySQL",
            value=os.getenv("MYSQL_HOST", DEFAULT_MYSQL_HOST),
            key="mysql_host",
        )
        st.number_input(
            "Port MySQL",
            min_value=1,
            max_value=65535,
            value=env_int("MYSQL_PORT", DEFAULT_MYSQL_PORT),
            key="mysql_port",
        )
        st.text_input(
            "User MySQL",
            value=os.getenv("MYSQL_USER", DEFAULT_MYSQL_USER),
            key="mysql_user",
        )
        st.text_input(
            "Password MySQL",
            value=os.getenv("MYSQL_PASSWORD", ""),
            type="password",
            key="mysql_password",
        )
        st.text_input(
            "Database",
            value=os.getenv("MYSQL_DATABASE", DEFAULT_MYSQL_DATABASE),
            key="mysql_database",
        )
        st.checkbox("Buat database jika belum ada", value=True, key="create_database")

        st.divider()
        st.header("Ollama")
        ollama_url = st.text_input(
            "Endpoint",
            value=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL),
        )
        model = st.text_input(
            "Model",
            value=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        )
        max_rows = st.slider("Maksimal baris hasil", 10, 1000, 100)

        if st.button("Tes koneksi", use_container_width=True):
            try:
                connection = MySqlRepository(get_mysql_config()).connect()
                connection.close()
                st.success("MySQL terhubung.")
            except Exception as exc:
                st.error(f"MySQL gagal: {exc}")

    return get_mysql_config(), ollama_url, model, max_rows
