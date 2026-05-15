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


def get_mysql_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.mysql_host,
        "port": int(st.session_state.mysql_port),
        "user": st.session_state.mysql_user,
        "password": st.session_state.mysql_password,
        "database": st.session_state.mysql_database,
        "create_database": st.session_state.create_database,
    }


def get_ollama_config() -> Dict[str, Any]:
    return {
        "host": st.session_state.ollama_host,
        "model": st.session_state.ollama_model,
    }


@st.dialog("Setting MYSQL & Ollama")
def show_dialog() -> None:
    st.header("MySQL")

    st.text_input(
        "Host MySQL", 
        key="mysql_host",
        value=st.session_state.mysql_host,
        )

    st.number_input(
        "Port MySQL",
        min_value=1,
        max_value=65535,
        value=st.session_state.mysql_port,
        key="mysql_port",
    )

    st.text_input(
        "User MySQL",
        key="mysql_user",
        value=st.session_state.mysql_user,
    )

    st.text_input(
        "Password MySQL",
        type="password",
        key="mysql_password",
        value=st.session_state.mysql_password,
    )

    st.text_input(
        "Database",
        key="mysql_database",
        value=st.session_state.mysql_database,
    )

    st.checkbox(
        "Buat database jika belum ada",
        key="create_database",
        value=st.session_state.create_database,
    )

    if st.button("Tes koneksi", use_container_width=True):
        try:
            connection = MySqlRepository(get_mysql_config()).connect()
            connection.close()
            st.success("MySQL terhubung.")
        except Exception as exc:
            st.error(f"MySQL gagal: {exc}")

    st.divider()
    st.header("Ollama")

    st.text_input(
        "Endpoint",
        key="ollama_host",
        value=st.session_state.ollama_host,
    )
    st.text_input(
        "Model",
        key="ollama_model",
        value=st.session_state.ollama_model,
    )

    st.slider(
        "Maksimal baris hasil",
        min_value=10,
        max_value=1000,
        key="max_rows",
    )

    if st.button("Simpan", type="primary", use_container_width=True):
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
            show_dialog()

    return (
        get_mysql_config(),
        st.session_state.ollama_host,
        st.session_state.ollama_model,
        st.session_state.max_rows,
    )