import streamlit as st
import json
import requests
import base64
from auth import login, exige_admin
from components.header import render_header

st.set_page_config(page_title="Gerenciar Usuários", layout="wide")
login()
render_header()
exige_admin()
st.title("👥 Gerenciar Usuários e Solicitações")

# ----------------------------
# GitHub
# ----------------------------
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
FILE_USERS = "data/usuarios.json"
FILE_SOLIC = "data/solicitacoes.json"
TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ----------------------------
# Funções GitHub
# ----------------------------
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
    r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{caminho}", json=payload, headers=HEADERS)
    if r.status_code not in (200, 201):
        st.error(r.json())
        st.stop()

# ----------------------------
# Carregar dados
# ----------------------------
solicitacoes, _ = carregar_github(FILE_SOLIC)
usuarios, _ = carregar_github(FILE_USERS)

# ----------------------------
# Filtrar pendentes
# ----------------------------
pendentes = {k: v for k, v in solicitacoes.items() if v.get("status") == "pendente"}

st.subheader("📬 Solicitações Pendentes")
if pendentes:
    aprovar_lista = []
    rejeitar_lista = []

    for nome, info in pendentes.items():
        st.markdown(f"### 👤 {nome}")
        st.write(f"📧 {info.get('email', '—')}")
        perfil = st.selectbox(f"Perfil para {nome}", ["USER", "ADMIN"], key=f"perfil_{nome}")

        col1, col2 = st.columns(2)
        if col1.button(f"✅ Aprovar {nome}", key=f"aprovar_{nome}"):
            aprovar_lista.append((nome, perfil))
        if col2.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{nome}"):
            rejeitar_lista.append(nome)

    # Processar aprovações fora do loop
    if aprovar_lista:
        for nome, perfil in aprovar_lista:
            usuarios[nome] = {
                "senha": solicitacoes[nome]["senha"],
                "perfil": perfil,
                "status": "ativo"
            }
            solicitacoes[nome]["status"] = "aprovado"
        salvar_github(usuarios, FILE_USERS, "Aprovação de usuários")
        salvar_github(solicitacoes, FILE_SOLIC, "Atualização das solicitações")
        st.success("✅ Usuários aprovados com sucesso!")
        st.experimental_rerun()

    if rejeitar_lista:
        for nome in rejeitar_lista:
            solicitacoes[nome]["status"] = "rejeitado"
        salvar_github(solicitacoes, FILE_SOLIC, "Rejeição de solicitações")
        st.warning("❌ Solicitações rejeitadas.")
        st.experimental_rerun()
else:
    st.info("📭 Nenhuma solicitação pendente no momento.")

# ----------------------------
# Usuários Ativos
# ----------------------------
st.subheader("👥 Usuários Cadastrados")
ativos = {k: v for k, v in usuarios.items() if v.get("status") == "ativo"}
remover_lista = []

for nome, info in ativos.items():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.write(f"👤 {nome}")
    with col2:
        st.write(info.get("perfil", "USER").upper())
    with col3:
        if nome != "admin" and st.button("🗑️", key=f"del_{nome}"):
            remover_lista.append(nome)

# Remover usuários fora do loop
if remover_lista:
    for nome in remover_lista:
        usuarios.pop(nome)
    salvar_github(usuarios, FILE_USERS, "Remoção de usuários")
    st.success("Usuários removidos com sucesso!")
    st.experimental_rerun()
