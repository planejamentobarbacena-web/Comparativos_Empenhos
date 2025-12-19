import streamlit as st
import json
import requests
import base64

st.set_page_config(page_title="Solicitar Acesso", layout="centered")
st.title("📝 Solicitar Acesso ao Sistema")

# ----------------------------
# Inputs do usuário
# ----------------------------
nome = st.text_input("Nome de usuário")

senha = st.text_input(
    "Senha",
    type="password",
    help="Sistema hospedado em ambiente público. Cadastre uma senha exclusiva, que não seja utilizada em sistemas pessoais ou institucionais."
)

st.markdown(
    """
    <div style="
        font-size: 16px;
        font-weight: 600;
        color: #333333;
        margin-top: -5px;
        margin-bottom: 15px;
    ">
        🔒 Sistema hospedado em ambiente público. 
        Cadastre uma senha exclusiva, que não seja utilizada em sistemas pessoais ou institucionais.
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Configuração GitHub
# ----------------------------
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
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
    return dados, info["sha"]

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
        st.error(r.json())
        st.stop()

# ----------------------------
# Botão de envio
# ----------------------------
if st.button("📨 Enviar solicitação"):
    if not nome or not senha:
        st.error("Preencha todos os campos!")
        st.stop()

    solicitacoes, _ = carregar_github(FILE_SOLIC)

    if nome in solicitacoes:
        st.warning("Este nome de usuário já possui uma solicitação pendente.")
        st.stop()

    solicitacoes[nome] = {
        "senha": senha,
        "perfil": "USER",
        "status": "pendente"
    }

    salvar_github(solicitacoes, FILE_SOLIC, f"Nova solicitação: {nome}")
    st.success("✅ Solicitação enviada! Aguarde aprovação do administrador.")
