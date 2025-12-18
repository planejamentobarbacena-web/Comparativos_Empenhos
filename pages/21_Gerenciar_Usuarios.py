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

# =========================
# CONFIGURAÇÃO GITHUB
# =========================
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
ARQUIVO = "data/usuarios.json"

TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =========================
# FUNÇÕES
# =========================
def carregar_usuarios():
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        st.error("❌ Erro ao carregar usuarios.json")
        st.stop()

    info = r.json()
    dados = json.loads(
        requests.get(info["download_url"]).text
    )

    return dados, info["sha"]


def salvar_usuarios(usuarios, sha, mensagem):
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO}"

    conteudo = base64.b64encode(
        json.dumps(usuarios, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    data = {
        "message": mensagem,
        "content": conteudo,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(url, json=data, headers=HEADERS)

    if r.status_code not in (200, 201):
        st.error(r.json())
        st.stop()


st.set_page_config(page_title="Gerenciar Usuários", layout="centered")
st.title("👥 Gerenciar Usuários")

# =========================
# CARREGA
# =========================
usuarios, sha_atual = carregar_usuarios()

# =========================
# LISTAGEM
# =========================
for nome, dados in usuarios.items():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    with col1:
        st.write(f"👤 **{nome}**")

    with col2:
        st.write(dados.get("perfil", "usuario").upper())

    with col3:
        st.write(dados.get("status", "pendente"))

    with col4:
        if nome != "admin":
            if dados.get("status") != "ativo":
                if st.button("✅", key=f"aprovar_{nome}"):
                    usuarios[nome]["status"] = "ativo"
                    salvar_usuarios(usuarios, sha_atual, f"Aprova usuário {nome}")
                    st.success(f"Usuário {nome} aprovado")
                    st.rerun()

            if st.button("🗑️", key=f"del_{nome}"):
                usuarios.pop(nome)
                salvar_usuarios(usuarios, sha_atual, f"Remove usuário {nome}")
                st.success(f"Usuário {nome} excluído")
                st.rerun()


