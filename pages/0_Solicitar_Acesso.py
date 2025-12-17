import streamlit as st
import json
import os

st.title("📝 Solicitar Acesso ao Sistema")

nome = st.text_input("Nome de usuário")
email = st.text_input("E-mail")
senha = st.text_input("Senha", type="password")

file_path = os.path.join(os.getcwd(), "solicitacoes.json")

# ==========================
# Funções seguras
# ==========================
def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ==========================
# Botão
# ==========================
if st.button("📨 Enviar solicitação"):
    if not nome or not email or not senha:
        st.error("Preencha todos os campos!")
        st.stop()

    solicitacoes = carregar_json(file_path)

    if nome in solicitacoes:
        st.warning("Este nome de usuário já possui uma solicitação pendente.")
        st.stop()

    solicitacoes[nome] = {
        "email": email,
        "senha": senha,
        "perfil": "USER",
        "status": "pendente"
    }

    salvar_json(file_path, solicitacoes)

    st.success("✅ Solicitação enviada! Aguarde aprovação do administrador.")
    st.stop()
