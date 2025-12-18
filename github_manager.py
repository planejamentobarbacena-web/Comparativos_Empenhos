import base64
import requests
import os

# ----------------------------
# CONFIGURAÇÃO
# ----------------------------
REPO = "planejamentobarbacena-web/Comparativos_Empenhos"
BRANCH = "master"

TOKEN = os.getenv("GITHUB_TOKEN")  # usa Secrets do Streamlit
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ----------------------------
# UPLOAD DE ARQUIVO
# ----------------------------
def upload_arquivo(conteudo_bytes, caminho_repo, mensagem="Adicionando arquivo"):
    conteudo_base64 = base64.b64encode(conteudo_bytes).decode("utf-8")

    url = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"

    data = {
        "message": mensagem,
        "content": conteudo_base64,
        "branch": BRANCH
    }

    r = requests.put(url, json=data, headers=HEADERS)

    if r.status_code not in [200, 201]:
        raise Exception(r.json())

    return r.json()

# ----------------------------
# EXCLUSÃO DE ARQUIVO
# ----------------------------
def excluir_arquivo(caminho_repo, mensagem="Removendo arquivo"):
    url = f"https://api.github.com/repos/{REPO}/contents/{caminho_repo}"

    r_get = requests.get(url, headers=HEADERS)
    if r_get.status_code != 200:
        raise Exception("Arquivo não encontrado no GitHub")

    sha = r_get.json()["sha"]

    data = {
        "message": mensagem,
        "sha": sha,
        "branch": BRANCH
    }

    r_del = requests.delete(url, json=data, headers=HEADERS)

    if r_del.status_code != 200:
        raise Exception(r_del.json())

    return r_del.json()
