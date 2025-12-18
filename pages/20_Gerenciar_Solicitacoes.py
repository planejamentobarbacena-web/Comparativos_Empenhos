import streamlit as st
import os
import json
from auth import login, exige_admin
from components.header import render_header

# 🔐 Segurança
login()
render_header()
exige_admin()

st.title("👥 Gerenciar Solicitações de Acesso")

# ----------------------------
# Caminhos dos arquivos JSON
# ----------------------------
file_solic = os.path.join("data", "solicitacoes.json")
file_users = os.path.join("data", "usuarios.json")

# ----------------------------
# Funções utilitárias
# ----------------------------
def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def sanitize_key(s):
    """Garante que o nome do usuário vire uma chave válida para widgets"""
    return "".join(c for c in s if c.isalnum() or c == "_")

def aprovar_usuario(nome, perfil):
    usuarios[nome] = {
        "senha": solicitacoes[nome]["senha"],
        "perfil": perfil,
        "status": "ativo"
    }
    solicitacoes[nome]["status"] = "aprovado"
    salvar_json(file_users, usuarios)
    salvar_json(file_solic, solicitacoes)
    st.success(f"✅ {nome} aprovado como {perfil}")

def rejeitar_usuario(nome):
    solicitacoes[nome]["status"] = "rejeitado"
    salvar_json(file_solic, solicitacoes)
    st.warning(f"❌ Solicitação de {nome} rejeitada.")

# ----------------------------
# Carregar dados
# ----------------------------
solicitacoes = carregar_json(file_solic)
usuarios = carregar_json(file_users)

# Filtrar pendentes
pendentes = {k: v for k, v in solicitacoes.items() if v.get("status") == "pendente"}

if not pendentes:
    st.info("📭 Nenhum cadastro solicitado no momento.")
    st.stop()

# ----------------------------
# Exibir solicitações pendentes
# ----------------------------
for nome, info in pendentes.items():
    st.markdown(f"### 👤 {nome}")
    st.write(f"📧 {info.get('email', '—')}")

    key_base = sanitize_key(nome)

    perfil_escolhido = st.selectbox(
        f"Perfil para {nome}",
        ["USER", "ADMIN"],
        key=f"perfil_{key_base}"
    )

    col1, col2 = st.columns(2)

    if col1.button(f"✅ Aprovar {nome}", key=f"aprovar_{key_base}"):
        aprovar_usuario(nome, perfil_escolhido)
        st.experimental_rerun()

    if col2.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{key_base}"):
        rejeitar_usuario(nome)
        st.experimental_rerun()
