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
