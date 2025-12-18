import streamlit as st
import os
import json
import requests
import base64
from auth import login, exige_admin
from components.header import render_header

# 🔐 Segurança
login()
render_header()
exige_admin()

st.set_page_config(page_title="Gerenciar Usuários e Solicitações", layout="wide")
st.title("👥 Gerenciar Usuários e Solicitações")

# =========================
# CONFIGURAÇÃO GITHUB
# =========================
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
FILE_SOLIC = "data/solicitacoes.json"
FILE_USERS = "data/usuarios.json"
TOKEN = st.secrets["GITHUB_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# =========================
# FUNÇÕES GITHUB
# =========================
def carregar_github(caminho):
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        st.error(f"❌ Erro ao carregar {caminho}")
        st.stop()
    info = r.json()
    dados = json.loads(requests.get(info["download_url"]).text)
    return dados, info["sha"]

def salvar_github(dados, caminho, mensagem):
    # Sempre pega o SHA mais recente
    _, sha_atual = carregar_github(caminho)
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho}"
    conteudo = base64.b64encode(json.dumps(dados, indent=2, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    payload = {"message": mensagem, "content": conteudo, "sha": sha_atual, "branch": BRANCH}
    r = requests.put(url, json=payload, headers=HEADERS)
    if r.status_code not in (200, 201):
        st.error(r.json())
        st.stop()

# =========================
# CARREGAR DADOS
# =========================
solicitacoes, _ = carregar_github(FILE_SOLIC)
usuarios, _ = carregar_github(FILE_USERS)

# -------------------------
# Separa pendentes e ativos
# -------------------------
pendentes = {k: v for k, v in solicitacoes.items() if v.get("status") == "pendente"}
ativos = {k: v for k, v in usuarios.items() if v.get("status") == "ativo"}

# =========================
# SEÇÃO 1: Solicitações Pendentes
# =========================
st.subheader("📭 Solicitações Pendentes")
if not pendentes:
    st.info("Nenhuma solicitação no momento.")
else:
    for nome, info in pendentes.items():
        st.markdown(f"### 👤 {nome}")
        st.write(f"📧 {info.get('email', '—')}")

        perfil_escolhido = st.selectbox(f"Perfil para {nome}", ["USER", "ADMIN"], key=f"perfil_{nome}")

        col1, col2 = st.columns(2)
        if col1.button(f"✅ Aprovar {nome}", key=f"aprovar_{nome}"):
            # Atualiza usuarios e solicitacoes
            usuarios[nome] = {"senha": info["senha"], "perfil": perfil_escolhido, "status": "ativo"}
            solicitacoes[nome]["status"] = "aprovado"

            # Salva no GitHub
            salvar_github(usuarios, FILE_USERS, f"Aprova usuário {nome}")
            salvar_github(solicitacoes, FILE_SOLIC, f"Aprova solicitação {nome}")

            st.success(f"{nome} aprovado como {perfil_escolhido}")
            st.experimental_rerun()

        if col2.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{nome}"):
            solicitacoes[nome]["status"] = "rejeitado"
            salvar_github(solicitacoes, FILE_SOLIC, f"Rejeita solicitação {nome}")
            st.warning(f"Solicitação de {nome} rejeitada.")
            st.experimental_rerun()

# =========================
# SEÇÃO 2: Usuários Cadastrados
# =========================
st.subheader("👥 Usuários Cadastrados")
if not ativos:
    st.info("Nenhum usuário ativo.")
else:
    for nome, info in ativos.items():
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"👤 **{nome}**")
        with col2:
            st.write(info.get("perfil", "USER").upper())
        with col3:
            if nome != "admin":
                if st.button("🗑️", key=f"del_{nome}"):
                    usuarios.pop(nome)
                    salvar_github(usuarios, FILE_USERS, f"Remove usuário {nome}")
                    st.success(f"Usuário {nome} excluído")
                    st.experimental_rerun()
