import streamlit as st

from ui.chat_view import render_chat
from ui.import_view import render_import
from ui.schema_view import render_schema
from ui.sidebar import render_sidebar


def main() -> None:
    st.set_page_config(page_title="Chatbot MySQL Ollama", layout="wide")
    st.title("Chatbot MySQL Ollama")

    mysql_config, ollama_url, model, max_rows = render_sidebar()

    chat_tab, import_tab, schema_tab, testing = st.tabs(["Chat", "Import", "Schema", "Testing"])
    with chat_tab:
        render_chat(mysql_config, ollama_url, model, max_rows)
    with import_tab:
        render_import(mysql_config)
    with schema_tab:
        render_schema(mysql_config)
    with testing:
        st.info("Fitur testing masih dalam pengembangan. Nantikan update selanjutnya!")

if __name__ == "__main__":
    main()
