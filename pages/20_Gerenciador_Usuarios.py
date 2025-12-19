import streamlit as st
import json
import requests
import base64
from auth import login, exige_admin
from components.header import render_header

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(page_title="Gerenciar Usuários", layout="wide")

login()
render_header()
exige_admin()

st.title("👥 Gerenciar Usuários e Solicitações")

# ============================
# CONFIGURAÇÃO GITHUB
# ============================
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"

FILE_USERS = "data/usuarios.json"
FILE_SOLIC = "data/solicitacoes.json"

TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ============================
# FUNÇÕES AUXILIARES
# ============================
def carregar_github(caminho):
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return {}, None
    info = r.json()
    dados = json.loads(requests.get(info["download_url"]).text)
    return dados, info.get("sha")


def salvar_github(dados, caminho, mensagem):
    _, sha_atual = carregar_github(caminho)
    conteudo = base64.b64encode(
        json.dumps(dados, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": mensagem,
        "content": conteudo,
        "sha": sha_atual,
        "branch": BRANCH
    }

    r = requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{caminho}",
        json=payload,
        headers=HEADERS
    )

    if r.status_code not in (200, 201):
        st.error("Erro ao salvar no GitHub")
        st.json(r.json())
        st.stop()

# ============================
# CARREGAR DADOS
# ============================
solicitacoes, _ = carregar_github(FILE_SOLIC)
usuarios, _ = carregar_github(FILE_USERS)

solicitacoes = solicitacoes or {}
usuarios = usuarios or {}

# ============================
# SOLICITAÇÕES PENDENTES
# ============================
pendentes = {
    nome: info
    for nome, info in solicitacoes.items()
    if isinstance(info, dict) and info.get("status") == "pendente"
}

st.subheader("📬 Solicitações Pendentes")

if not pendentes:
    st.info("📭 Nenhuma solicitação pendente no momento.")
else:
    for nome, info in pendentes.items():
        st.markdown(f"### 👤 {nome}")

        perfil_escolhido = st.selectbox(
            f"Perfil do usuário **{nome}**",
            ["USER", "ADMIN"],
            key=f"perfil_{nome}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"✅ Aprovar {nome}", key=f"aprovar_{nome}"):
                usuarios[nome] = {
                    "senha": info["senha"],
                    "perfil": perfil_escolhido,
                    "status": "ativo"
                }
                solicitacoes[nome]["status"] = "aprovado"

                salvar_github(usuarios, FILE_USERS, f"Aprovação do usuário {nome}")
                salvar_github(solicitacoes, FILE_SOLIC, f"Aprovação da solicitação {nome}")

                st.success(f"Usuário **{nome}** aprovado com sucesso!")
                st.experimental_rerun()

        with col2:
            if st.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{nome}"):
                solicitacoes[nome]["status"] = "rejeitado"
                salvar_github(solicitacoes, FILE_SOLIC, f"Rejeição da solicitação {nome}")
                st.warning(f"Solicitação de **{nome}** rejeitada.")
                st.experimental_rerun()

# ============================
# USUÁRIOS ATIVOS
# ============================
st.divider()
st.subheader("👥 Usuários Ativos")

ativos = {
    nome: info
    for nome, info in usuarios.items()
    if isinstance(info, dict) and info.get("status") == "ativo"
}

if not ativos:
    st.info("Nenhum usuário ativo cadastrado.")
else:
    remover = []

    for nome, info in ativos.items():
        col1, col2, col3 = st.columns([4, 2, 1])

        with col1:
            st.write(f"👤 {nome}")

        with col2:
            st.write(info.get("perfil", "USER"))

        with col3:
            if nome != "admin":
                if st.button("🗑️", key=f"del_{nome}"):
                    remover.append(nome)

    if remover:
        for nome in remover:
            usuarios.pop(nome, None)

        salvar_github(usuarios, FILE_USERS, "Remoção de usuários")
        st.success("Usuário(s) removido(s) com sucesso!")
        st.experimental_rerun()
