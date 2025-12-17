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

st.set_page_config(page_title="Gerenciar CSV", layout="centered")

st.title("🗂️ Gerenciar Exercícios (CSV)")

PASTA_DATA = Path("data")

if not PASTA_DATA.exists():
    st.warning("Pasta /data não encontrada.")
    st.stop()

arquivos = sorted(PASTA_DATA.glob("*.csv"))

if not arquivos:
    st.info("Nenhum arquivo CSV encontrado.")
    st.stop()

st.subheader("📄 Arquivos disponíveis")

for arq in arquivos:
    col1, col2 = st.columns([4, 1])

    with col1:
        st.write(f"📁 {arq.name}")

    with col2:
        if st.button("🗑️ Excluir", key=f"del_{arq.name}"):
            st.session_state["arquivo_para_excluir"] = arq.name

# ======================================================
# CONFIRMAÇÃO
# ======================================================
if "arquivo_para_excluir" in st.session_state:
    nome = st.session_state["arquivo_para_excluir"]
    caminho = PASTA_DATA / nome

    st.warning(f"⚠️ Deseja realmente excluir o arquivo **{nome}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Sim, excluir definitivamente"):
            try:
                caminho.unlink()
                st.success(f"✅ Arquivo {nome} excluído.")
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")

            del st.session_state["arquivo_para_excluir"]
            st.rerun()

    with col2:
        if st.button("❌ Cancelar"):
            del st.session_state["arquivo_para_excluir"]
            st.info("Exclusão cancelada.")
