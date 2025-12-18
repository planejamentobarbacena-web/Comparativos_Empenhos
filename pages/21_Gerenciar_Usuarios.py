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
    dados = json.loads(requests.get(info["download_url"]).text)
    return dados, info["sha"]

def salvar_usuarios(usuarios, mensagem):
    """
    Salva o JSON no GitHub e retorna o novo SHA
    """
    sha = carregar_usuarios()[1]  # obtém SHA atual antes de salvar
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
        st.error(f"❌ Erro ao salvar: {r.json()}")
        st.stop()

    return r.json()["content"]["sha"]

# =========================
# LAYOUT
# =========================
st.set_page_config(page_title="Gerenciar Usuários", layout="centered")
st.title("👥 Gerenciar Usuários")

# =========================
# CARREGAR USUÁRIOS
# =========================
usuarios, sha_atual = carregar_usuarios()

if not usuarios:
    st.info("Nenhum usuário cadastrado ainda.")
    st.stop()

# =========================
# LISTAGEM
# =========================
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
            # Botão Aprovar
            if dados.get("status") != "ativo":
                if st.button("✅", key=f"aprovar_{nome}"):
                    usuarios[nome]["status"] = "ativo"
                    sha_atual = salvar_usuarios(usuarios, f"Aprova usuário {nome}")
                    st.success(f"Usuário {nome} aprovado")
                    st.experimental_rerun()

            # Botão Excluir
            if st.button("🗑️", key=f"del_{nome}"):
                usuarios.pop(nome)
                sha_atual = salvar_usuarios(usuarios, f"Remove usuário {nome}")
                st.success(f"Usuário {nome} excluído")
                st.experimental_rerun()
