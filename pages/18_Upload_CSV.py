import streamlit as st
from github_manager import upload_arquivo, excluir_arquivo

st.title("📤 Gerenciar CSVs no GitHub")

# ---------------------------
# UPLOAD
# ---------------------------
arquivo = st.file_uploader("Selecione um CSV", type=["csv"])

if arquivo:
    if st.button("Enviar CSV para o GitHub"):
        caminho_local = f"/tmp/{arquivo.name}"

        with open(caminho_local, "wb") as f:
            f.write(arquivo.getbuffer())

        resultado = upload_arquivo(
            caminho_local,
            f"data/{arquivo.name}",
            mensagem=f"Upload {arquivo.name}"
        )

        if "commit" in resultado:
            st.success("✅ Upload realizado com sucesso!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ Erro no upload: {resultado}")


# ---------------------------
# EXCLUSÃO
# ---------------------------
st.divider()
st.subheader("🗑️ Excluir CSV")

arquivo_excluir = st.text_input("Nome do CSV (ex: 2024_empenhos.csv)")

if st.button("Excluir CSV do GitHub") and arquivo_excluir:
    caminho_repo = f"data/{arquivo_excluir.strip()}"

    resultado = excluir_arquivo(
        caminho_repo,
        mensagem=f"Remoção {arquivo_excluir}"
    )

    if "commit" in resultado:
        st.success("🗑️ Arquivo removido com sucesso!")
        st.cache_data.clear()
        st.rerun()
    else:
        st.error(f"❌ Erro na exclusão: {resultado}")
