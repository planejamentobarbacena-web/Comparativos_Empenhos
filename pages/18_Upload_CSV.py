import streamlit as st
import os
import json
from pathlib import Path 
from auth import login, exige_admin
from components.header import render_header

# 🔐 Segurança
login()
render_header()
exige_admin()

st.set_page_config(page_title="Upload de CSV", layout="centered")


st.title("📤 Enviar arquivos CSV de Empenhos")

PASTA_DATA = Path("data")
PASTA_DATA.mkdir(exist_ok=True)

arquivo = st.file_uploader(
    "Selecione o arquivo CSV",
    type=["csv"]
)

if arquivo:
    nome = arquivo.name
    caminho = PASTA_DATA / nome

    # Guarda o arquivo em memória
    if "arquivo_upload" not in st.session_state:
        st.session_state.arquivo_upload = None
        st.session_state.confirmar_substituicao = False

    st.session_state.arquivo_upload = arquivo

    if caminho.exists():
        st.warning(f"⚠️ O arquivo **{nome}** já existe.")

        if not st.session_state.confirmar_substituicao:
            if st.button("✅ Sim, substituir"):
                st.session_state.confirmar_substituicao = True
                st.rerun()

            if st.button("❌ Cancelar"):
                st.session_state.arquivo_upload = None
                st.session_state.confirmar_substituicao = False
                st.info("Operação cancelada.")
        else:
            with open(caminho, "wb") as f:
                f.write(st.session_state.arquivo_upload.getbuffer())

            st.success(f"✅ Arquivo **{nome}** substituído com sucesso.")
            st.session_state.confirmar_substituicao = False
            st.session_state.arquivo_upload = None

    else:
        with open(caminho, "wb") as f:
            f.write(arquivo.getbuffer())

        st.success(f"✅ Arquivo **{nome}** enviado com sucesso.")
