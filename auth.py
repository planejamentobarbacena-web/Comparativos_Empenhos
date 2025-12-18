import streamlit as st
import json
from pathlib import Path

# 📁 Arquivo de usuários agora fica na pasta data
USERS_FILE = Path("data/usuarios.json")


def carregar_usuarios():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_usuarios(usuarios: dict):
    USERS_FILE.parent.mkdir(exist_ok=True)  # garante pasta data
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


def login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.session_state.perfil = None

    if st.session_state.autenticado:
        return

    st.title("🔐 Acesso ao Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuarios = carregar_usuarios()

        if (
            usuario in usuarios
            and usuarios[usuario]["senha"] == senha
            and usuarios[usuario].get("status") == "ativo"
        ):
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.session_state.perfil = usuarios[usuario]["perfil"].upper()
            st.rerun()
        else:
            st.error("Usuário, senha inválidos ou acesso não aprovado")

    st.stop()


def logout():
    if st.sidebar.button("🚪 Sair"):
        for k in ["autenticado", "usuario", "perfil"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


def exige_admin():
    if st.session_state.get("perfil") != "ADMIN":
        st.error("⛔ Acesso restrito ao administrador.")
        st.stop()
