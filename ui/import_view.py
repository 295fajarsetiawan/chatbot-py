import pandas as pd
import streamlit as st

from repositories.mysql_repository import MySqlRepository
from services.import_service import ImportService


def render_import(mysql_config) -> None:
    st.subheader("Import Data")
    uploaded_file = st.file_uploader(
        "File CSV, Excel, atau SQL",
        type=["csv", "xlsx", "xls", "sql"],
    )

    if uploaded_file is None:
        return

    service = ImportService(MySqlRepository(mysql_config))

    if uploaded_file.name.lower().endswith(".sql"):
        render_sql_import(service, uploaded_file)
        return

    raw_table_name = st.text_input("Nama tabel tujuan", value="import_data")

    try:
        preview = service.prepare_upload(uploaded_file, raw_table_name)
    except Exception as exc:
        st.error(f"File gagal dibaca: {exc}")
        return

    st.caption(f"Tabel tujuan: `{preview.table_name}`")
    with st.expander("Mapping kolom"):
        mapping_df = pd.DataFrame(
            [
                {"kolom_file": key, "kolom_mysql": value}
                for key, value in preview.column_mapping.items()
            ]
        )
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)

    st.dataframe(preview.dataframe.head(50), use_container_width=True)

    if st.button("Import ke MySQL", type="primary", use_container_width=True):
        try:
            result = service.import_preview(preview)
            status = "Tabel dibuat" if result.created_table else "Tabel sudah ada"

            if result.created_columns:
                st.success(
                    f"{status}. {len(result.created_columns)} kolom baru siap. "
                    f"{result.inserted} baris berhasil diinsert."
                )
            else:
                st.success(f"{status}. {result.inserted} baris berhasil diinsert.")
        except Exception as exc:
            st.error(f"Import gagal: {exc}")


def render_sql_import(service: ImportService, uploaded_file) -> None:
    try:
        preview = service.prepare_sql_upload(uploaded_file)
    except Exception as exc:
        st.error(f"File SQL gagal dibaca: {exc}")
        return

    st.caption(f"File SQL: `{preview.file_name}`")
    st.info(f"Terdeteksi {len(preview.statements)} statement SQL.")

    auto_create_tables = st.checkbox(
        "Buat tabel otomatis jika INSERT mengarah ke tabel yang belum ada",
        value=True,
    )
    create_table_if_not_exists = st.checkbox(
        "Ubah CREATE TABLE menjadi CREATE TABLE IF NOT EXISTS",
        value=True,
    )
    insert_ignore = st.checkbox(
        "Abaikan data duplikat dengan INSERT IGNORE",
        value=False,
    )

    with st.expander("Preview SQL"):
        st.code(preview.script[:8000], language="sql")
        if len(preview.script) > 8000:
            st.caption("Preview dipotong sampai 8000 karakter.")

    if st.button("Import SQL ke MySQL", type="primary", use_container_width=True):
        try:
            result = service.import_sql_preview(
                preview,
                auto_create_tables=auto_create_tables,
                create_table_if_not_exists=create_table_if_not_exists,
                insert_ignore=insert_ignore,
            )

            if result.created_tables:
                st.success(
                    "Tabel otomatis dibuat: "
                    + ", ".join(f"`{table}`" for table in result.created_tables)
                )
            if result.created_columns:
                with st.expander("Kolom otomatis dibuat"):
                    for table, columns in result.created_columns.items():
                        st.write(f"- `{table}`: " + ", ".join(f"`{column}`" for column in columns))

            if result.skipped_reasons:
                st.warning(
                    f"{len(result.skipped_reasons)} statement dilewati. "
                    f"{result.executed} statement berhasil dijalankan."
                )
                with st.expander("Statement yang dilewati"):
                    for reason in result.skipped_reasons:
                        st.write(f"- {reason}")
            else:
                st.success(f"{result.executed} statement SQL berhasil dijalankan.")
        except Exception as exc:
            st.error(f"Import SQL gagal: {exc}")
