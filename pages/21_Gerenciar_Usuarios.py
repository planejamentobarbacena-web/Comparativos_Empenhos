import streamlit as st
import json
import requests
from auth import login, exige_admin
from components.header import render_header

# =========================
# CONFIGURAÇÃO GITHUB
# =========================
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
ARQUIVO_USUARIOS = "data/usuarios.json"

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =========================
# FUNÇÕES AUXILIARES
# =========================
def carregar_usuarios():
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_USUARIOS}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        st.error("❌ Não foi possível carregar usuarios.json")
        st.stop()

    conteudo = r.json()
    dados = json.loads(
        requests.get(conteudo["download_url"]).text
    )

    return dados, conteudo["sha"]


def salvar_usuarios(usuarios, sha, mensagem):
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_USUARIOS}"

    conteudo_base64 = (
        json.dumps(usuarios, indent=2, ensure_ascii=False)
        .encode("utf-8")
    )

    data = {
        "message": mensagem,
        "content": conteudo_base64.decode("utf-8").encode("utf-8").hex(),
        "sha": sha,
        "branch": BRANCH
    }

    # GitHub exige base64, então corrigimos:
    import base64
    data["content"] = base64.b64encode(
        json.dumps(usuarios, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    r = requests.put(url, json=data, headers=HEADERS)

    if r.status_code not in (200, 201):
        st.error(r.json())
        st.stop()


# =========================
# SEGURANÇA
# =========================
login()
render_header()
exige_admin()

st.set_page_config(page_title="Gerenciar Usuários", layout="centered")
st.title("👥 Gerenciar Usuários do Sistema")

# =========================
# CARREGA DADOS
# =========================
usuarios, sha_atual = carregar_usuarios()

if not usuarios:
    st.info("Nenhum usuário cadastrado.")
    st.stop()

# =========================
# LISTAGEM
# =========================
st.subheader("📄 Usuários cadastrados")

for idx, u in enumerate(usuarios):
    col1, col2, col3 = st.columns([4, 2, 1])

    with col1:
        st.write(f"👤 **{u.get('usuario')}**")

    with col2:
        st.write(u.get("perfil", "usuario"))

    with col3:
        if u.get("usuario") != "admin":
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state["usuario_excluir"] = idx

# =========================
# CONFIRMAÇÃO DE EXCLUSÃO
# =========================
if "usuario_excluir" in st.session_state:
    idx = st.session_state["usuario_excluir"]
    usuario = usuarios[idx]["usuario"]

    st.warning(f"⚠️ Deseja excluir o usuário **{usuario}**?")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("✅ Confirmar exclusão"):
            usuarios.pop(idx)

            salvar_usuarios(
                usuarios,
                sha_atual,
                f"Remoção do usuário {usuario}"
            )

            st.success("Usuário removido com sucesso.")
            del st.session_state["usuario_excluir"]
            st.cache_data.clear()
            st.rerun()

    with c2:
        if st.button("❌ Cancelar"):
            del st.session_state["usuario_excluir"]
            st.info("Exclusão cancelada.")
