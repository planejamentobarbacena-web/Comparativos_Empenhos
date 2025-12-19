import streamlit as st
import os
import shutil
import pandas as pd

st.set_page_config(
    page_title="📤 Upload de Referências",
    layout="centered"
)

st.title("📂 Upload de Arquivo de Referências")

# Caminho da pasta de dados
DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Upload do arquivo
arquivo = st.file_uploader("Selecione o arquivo XLSX", type=["xlsx"])

if arquivo is not None:
    if st.button("📤 Enviar Arquivo"):
        try:
            destino = os.path.join(DATA_DIR, arquivo.name)

            # Substitui arquivo se já existir
            with open(destino, "wb") as f:
                f.write(arquivo.getbuffer())

            st.success(f"✅ Arquivo '{arquivo.name}' enviado com sucesso!")

            # Limpa cache se você tiver funções de carregamento
            if "load_referencias" in st.session_state:
                del st.session_state["load_referencias"]
            st.cache_data.clear()

            # Teste rápido de leitura
            df = pd.read_excel(destino)
            st.info(f"✅ Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas")
            st.dataframe(df.head())

        except Exception as e:
            st.error(f"❌ Erro no upload: {e}")
