import streamlit as st
import json
import requests
import base64

from auth import login, exige_admin
from components.header import render_header

# 🔐 Segurança
login()
render_header()
exige_admin()

st.set_page_config(
    page_title="Gerenciar Usuários",
    layout="wide"
)

st.title("👥 Gerenciar Solicitações e Usuários")

# =========================
# CONFIGURAÇÃO GITHUB
# =========================
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
ARQ_USUARIOS = "data/usuarios.json"
ARQ_SOLIC = "data/solicitacoes.json"

TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =========================
# FUNÇÕES GITHUB / JSON
# =========================
def carregar_json_github(caminho):
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return {}, None
    info = r.json()
    dados = json.loads(requests.get(info["download_url"]).text)
    return dados, info["sha"]

def salvar_json_github(caminho, dados, mensagem):
    _, sha_atual = carregar_json_github(caminho)
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho}"
    conteudo = base64.b64encode(json.dumps(dados, indent=2, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    data = {"message": mensagem, "content": conteudo, "sha": sha_atual, "branch": BRANCH}
    r = requests.put(url, json=data, headers=HEADERS)
    if r.status_code not in (200, 201):
        st.error(f"❌ Erro ao salvar {caminho}: {r.json()}")
        st.stop()

# =========================
# CARREGAR DADOS
# =========================
usuarios, _ = carregar_json_github(ARQ_USUARIOS)
solicitacoes, _ = carregar_json_github(ARQ_SOLIC)

if usuarios is None:
    usuarios = {}
if solicitacoes is None:
    solicitacoes = {}

# =========================
# SEÇÃO 1: Solicitações Pendentes
# =========================
st.subheader("📭 Solicitações Pendentes")

pendentes = {k: v for k, v in solicitacoes.items() if v.get("status") == "pendente"}

if not pendentes:
    st.info("Nenhuma solicitação pendente no momento.")
else:
    for nome, info in pendentes.items():
        st.markdown(f"### 👤 {nome}")
        st.write(f"📧 {info.get('email', '—')}")
        perfil_escolhido = st.selectbox(f"Perfil para {nome}", ["USER", "ADMIN"], key=f"perfil_{nome}")

        col1, col2 = st.columns(2)

        if col1.button(f"✅ Aprovar {nome}", key=f"aprovar_{nome}"):
            # Atualiza usuários e solicitações
            usuarios[nome] = {
                "senha": info["senha"],
                "perfil": perfil_escolhido,
                "status": "ativo"
            }
            solicitacoes[nome]["status"] = "aprovado"
            salvar_json_github(ARQ_USUARIOS, usuarios, f"Aprova usuário {nome}")
            salvar_json_github(ARQ_SOLIC, solicitacoes, f"Aprova solicitação {nome}")
            st.success(f"✅ {nome} aprovado como {perfil_escolhido}")
            st.experimental_rerun()

        if col2.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{nome}"):
            solicitacoes[nome]["status"] = "rejeitado"
            salvar_json_github(ARQ_SOLIC, solicitacoes, f"Rejeita solicitação {nome}")
            st.warning(f"❌ Solicitação de {nome} rejeitada")
            st.experimental_rerun()

st.divider()

# =========================
# SEÇÃO 2: Usuários Ativos / Pendentes
# =========================
st.subheader("👥 Usuários Cadastrados")

if not usuarios:
    st.info("Nenhum usuário cadastrado ainda.")
else:
    for nome, dados in usuarios.items():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"👤 **{nome}**")
        with col2:
            st.write(dados.get("perfil", "USER").upper())
        with col3:
            st.write(dados.get("status", "pendente"))
        with col4:
            if nome != "admin":
                # Aprovar usuário pendente
                if dados.get("status") != "ativo":
                    if st.button("✅", key=f"aprovar_user_{nome}"):
                        usuarios[nome]["status"] = "ativo"
                        salvar_json_github(ARQ_USUARIOS, usuarios, f"Aprova usuário {nome}")
                        st.success(f"Usuário {nome} aprovado")
                        st.experimental_rerun()

                # Excluir usuário
                if st.button("🗑️", key=f"del_user_{nome}"):
                    usuarios.pop(nome)
                    salvar_json_github(ARQ_USUARIOS, usuarios, f"Remove usuário {nome}")
                    st.success(f"Usuário {nome} excluído")
                    st.experimental_rerun()
