import streamlit as st

from repositories.mysql_repository import MySqlRepository


def render_schema(mysql_config) -> None:
    st.subheader("Schema")

    if st.button("Refresh schema", use_container_width=True):
        repository = MySqlRepository(mysql_config)
        try:
            connection = repository.connect()
            try:
                st.session_state.schema_tables = repository.list_tables(connection)
                st.session_state.schema_text = repository.get_schema_summary(connection)
            finally:
                connection.close()
        except Exception as exc:
            st.error(f"Schema gagal dibaca: {exc}")
            return

    tables = st.session_state.get("schema_tables")
    schema = st.session_state.get("schema_text")

    if tables is None:
        st.info("Klik refresh untuk membaca schema.")
        return

    if not tables:
        st.info("Belum ada tabel.")
        return

    st.code(schema, language="text")
