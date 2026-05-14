import pandas as pd
import streamlit as st

from repositories.mysql_repository import MySqlRepository
from services.chat_service import ChatService
from services.ollama_service import OllamaService


def render_chat(mysql_config, ollama_url: str, model: str, max_rows: int) -> None:
    st.subheader("Chat Query Database")
    st.info(
        "Chat mendukung SELECT, INSERT, UPDATE, dan DELETE. "
        "Untuk keamanan, UPDATE dan DELETE wajib memakai kondisi WHERE."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render semua message
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("sql"):
                st.markdown("**Deskripsi hasil**")

            st.markdown(message["content"])

            if message.get("sql"):
                st.code(message["sql"], language="sql")

            if isinstance(message.get("dataframe"), pd.DataFrame):
                st.dataframe(
                    message["dataframe"],
                    use_container_width=True,
                    hide_index=True,
                )

            elif message.get("operation") in {"insert", "update", "delete"}:
                st.info(
                    f"Operasi {message['operation'].upper()} selesai. "
                    f"{message.get('affected_rows', 0)} baris terdampak."
                )

    # TARUH DI PALING BAWAH
    question = st.chat_input("Tanya data di database")

    if not question:
        return

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            service = ChatService(
                MySqlRepository(mysql_config),
                OllamaService(ollama_url, model),
            )

            with st.spinner("Membuat SQL dan mengambil data..."):
                result = service.ask(question, max_rows)

            st.markdown("**Deskripsi hasil**")
            st.markdown(result.explanation)
            st.code(result.sql, language="sql")

            if isinstance(result.dataframe, pd.DataFrame):
                st.dataframe(
                    result.dataframe,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    f"Operasi {result.operation.upper()} selesai. "
                    f"{result.affected_rows} baris terdampak."
                )

            st.session_state.messages.append(
                {
                    "affected_rows": result.affected_rows,
                    "role": "assistant",
                    "content": result.explanation,
                    "operation": result.operation,
                    "sql": result.sql,
                    "dataframe": result.dataframe,
                }
            )

        except Exception as exc:
            error_message = (
                f"Gagal membuat atau menjalankan query: {exc}"
            )

            st.error(error_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                }
            )