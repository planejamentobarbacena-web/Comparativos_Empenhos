import streamlit as st
import os
import pandas as pd
import base64
import requests

st.set_page_config(
    page_title="📤 Upload de Referências",
    layout="centered"
)

st.title("📂 Upload de Arquivo de Referências")

# ----------------------------
# Configuração GitHub
# ----------------------------
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"
PASTA = "data"
TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ----------------------------
# Pasta local
# ----------------------------
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------
# Funções GitHub
# ----------------------------
def salvar_github(nome_arquivo, conteudo_bytes, mensagem):
    caminho_repo = f"{PASTA}/{nome_arquivo}"
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"

    r = requests.get(url, headers=HEADERS)
    sha = r.json()["sha"] if r.status_code == 200 else None

    conteudo_b64 = base64.b64encode(conteudo_bytes).decode("utf-8")

    data = {
        "message": mensagem,
        "content": conteudo_b64,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=HEADERS, json=data)
    if r.status_code not in (200, 201):
        st.error(f"❌ Erro ao enviar para GitHub: {r.json()}")
        return False
    return True

# ----------------------------
# Controle de envio
# ----------------------------
if "arquivo_enviado" not in st.session_state:
    st.session_state["arquivo_enviado"] = False

if not st.session_state["arquivo_enviado"]:
    arquivo = st.file_uploader("Selecione o arquivo XLSX", type=["xlsx"])
    if arquivo is not None and st.button("📤 Enviar Arquivo"):
        try:
            destino = os.path.join(DATA_DIR, arquivo.name)
            with open(destino, "wb") as f:
                f.write(arquivo.getbuffer())

            sucesso_github = salvar_github(arquivo.name, arquivo.getvalue(), f"Upload {arquivo.name}")

            df = pd.read_excel(destino)

            if sucesso_github:
                st.success(f"✅ Arquivo '{arquivo.name}' enviado com sucesso!")
            else:
                st.warning("Arquivo salvo localmente, mas não foi possível enviar para o GitHub.")

            st.dataframe(df.head())
            st.session_state["arquivo_enviado"] = True

        except Exception as e:
            st.error(f"❌ Erro no upload: {e}")

else:
    st.info("📌 Arquivo já enviado. Para enviar outro, atualize a página ou clique abaixo.")
    if st.button("📂 Enviar novo arquivo"):
        st.session_state["arquivo_enviado"] = False
        st.experimental_rerun()

