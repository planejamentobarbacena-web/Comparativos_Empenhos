import streamlit as st
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
    st.write(f"📁 {arq.name}")

st.divider()

st.info(
    "📌 **Observação:** o envio e a exclusão de arquivos CSV "
    "devem ser realizados exclusivamente pela página **Atualizar CSV**."
)
