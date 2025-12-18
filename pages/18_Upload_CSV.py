import streamlit as st
from auth import login, exige_admin
from github_manager import upload_arquivo, excluir_arquivo

# ----------------------------
# Segurança
# ----------------------------
login()
exige_admin()

st.set_page_config(page_title="Gerenciar CSVs", layout="centered")

st.title("📂 Gerenciar arquivos CSV (GitHub)")

st.markdown(
    """
    - Upload e exclusão **afetam diretamente o GitHub**
    - Os painéis refletem automaticamente as mudanças
    """
)

st.divider()

# ======================================================
# UPLOAD
# ======================================================
st.subheader("📤 Enviar novo CSV")

arquivo = st.file_uploader(
    "Selecione um arquivo CSV",
    type=["csv"]
)

if arquivo:
    try:
        upload_arquivo(
            conteudo_bytes=arquivo.getbuffer(),
            caminho_repo=f"data/{arquivo.name}",
            mensagem=f"Adiciona {arquivo.name}"
        )
        st.success(f"✅ Arquivo **{arquivo.name}** enviado com sucesso!")
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"Erro no upload: {e}")

st.divider()

# ======================================================
# EXCLUSÃO
# ======================================================
st.subheader("🗑️ Excluir CSV do GitHub")

nome_excluir = st.text_input(
    "Nome do arquivo (ex: 2024_empenhos.csv)"
)

if st.button("❌ Excluir arquivo"):
    if not nome_excluir:
        st.warning("Informe o nome do arquivo.")
    else:
        try:
            excluir_arquivo(
                caminho_repo=f"data/{nome_excluir}",
                mensagem=f"Remove {nome_excluir}"
            )
            st.success(f"🗑️ Arquivo **{nome_excluir}** removido com sucesso!")
            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao excluir: {e}")
