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
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------------------
# Funções GitHub
# ----------------------------
def salvar_github(nome_arquivo, conteudo_bytes, mensagem):
    caminho_repo = f"{PASTA}/{nome_arquivo}"
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"

    # Verificar se já existe para obter SHA
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
    else:
        st.success(f"✅ Arquivo '{nome_arquivo}' enviado para o GitHub com sucesso!")

# ----------------------------
# Upload do arquivo
# ----------------------------
arquivo = st.file_uploader("Selecione o arquivo XLSX", type=["xlsx"])

if arquivo is not None:
    if st.button("📤 Enviar Arquivo"):
        try:
            # ------------------------
            # Salva local
            # ------------------------
            destino = os.path.join(DATA_DIR, arquivo.name)
            with open(destino, "wb") as f:
                f.write(arquivo.getbuffer())
            st.success(f"✅ Arquivo '{arquivo.name}' salvo localmente.")

            # ------------------------
            # Salva no GitHub
            # ------------------------
            salvar_github(arquivo.name, arquivo.getvalue(), f"Upload {arquivo.name}")

            # ------------------------
            # Teste rápido de leitura
            # ------------------------
            df = pd.read_excel(destino)
            st.info(f"✅ Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas")
            st.dataframe(df.head())

        except Exception as e:
            st.error(f"❌ Erro no upload: {e}")
