import streamlit as st
from github_manager import upload_arquivo, excluir_arquivo

st.title("📤 Gerenciar CSVs no GitHub")

# ----------------------------
# UPLOAD
# ----------------------------
arquivo = st.file_uploader("Selecione um CSV", type=["csv"])

if arquivo:
    try:
        resultado = upload_arquivo(
            conteudo_bytes=arquivo.getvalue(),
            caminho_repo=f"data/{arquivo.name}",
            mensagem=f"Upload do arquivo {arquivo.name}"
        )
        st.success(f"Arquivo {arquivo.name} enviado com sucesso!")
    except Exception as e:
        st.error(f"Erro no upload: {e}")

# ----------------------------
# EXCLUSÃO
# ----------------------------
st.divider()
arquivo_excluir = st.text_input("Nome do CSV para excluir (ex: data/meuarquivo.csv)")

if st.button("Excluir CSV do GitHub") and arquivo_excluir:
    try:
        excluir_arquivo(arquivo_excluir)
        st.success(f"Arquivo {arquivo_excluir} removido do GitHub.")
    except Exception as e:
        st.error(f"Erro na exclusão: {e}")
