import base64
import requests
import os
import streamlit as st

# ----------------------------
# CONFIGURAÇÃO
# ----------------------------
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"

# 🔐 TOKEN vem do ambiente / secrets
TOKEN = st.secrets.get("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError("Token do GitHub não configurado")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# ----------------------------
# FUNÇÃO PARA UPLOAD
# ----------------------------
def upload_arquivo(caminho_local, caminho_repo, mensagem="Adicionando arquivo"):
    with open(caminho_local, "rb") as f:
        conteudo = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"
    data = {
        "message": mensagem,
        "content": conteudo,
        "branch": BRANCH
    }

    r = requests.put(url, json=data, headers=HEADERS)
    return r.json()

# ----------------------------
# FUNÇÃO PARA EXCLUIR
# ----------------------------
def excluir_arquivo(caminho_repo, mensagem="Removendo arquivo"):
    # pega o SHA do arquivo
    url_get = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"
    r = requests.get(url_get, headers=HEADERS)
    if r.status_code != 200:
        return {"erro": f"Arquivo não encontrado: {caminho_repo}"}
    sha = r.json()["sha"]

    url = url_get
    data = {
        "message": mensagem,
        "sha": sha,
        "branch": BRANCH
    }
    r = requests.delete(url, json=data, headers=HEADERS)
    return r.json()
