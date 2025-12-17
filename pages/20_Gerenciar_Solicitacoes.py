import streamlit as st
import os
import json
from auth import login, exige_admin
from components.header import render_header

# 🔐 Segurança
login()
render_header()
exige_admin()

st.title("👥 Gerenciar Solicitações de Acesso")

file_solic = os.path.join(os.getcwd(), "solicitacoes.json")
file_users = os.path.join(os.getcwd(), "usuarios.json")

# ==========================
# Função segura para JSON
# ==========================
def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

# Carregar dados
solicitacoes = carregar_json(file_solic)
usuarios = carregar_json(file_users)

# ==========================
# Filtrar pendentes
# ==========================
pendentes = {
    k: v for k, v in solicitacoes.items()
    if v.get("status") == "pendente"
}

if not pendentes:
    st.info("📭 Nenhum cadastro solicitado no momento.")
    st.stop()

# ==========================
# Exibir solicitações
# ==========================
for nome, info in pendentes.items():
    st.markdown(f"### 👤 {nome}")
    st.write(f"📧 {info.get('email', '—')}")

    perfil_escolhido = st.selectbox(
        f"Perfil para {nome}",
        ["USER", "ADMIN"],
        key=f"perfil_{nome}"
    )

    col1, col2 = st.columns(2)

    if col1.button(f"✅ Aprovar {nome}", key=f"aprovar_{nome}"):
        usuarios[nome] = {
            "senha": info["senha"],
            "perfil": perfil_escolhido,
            "status": "ativo"
        }
        info["status"] = "aprovado"

        with open(file_users, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=4, ensure_ascii=False)

        with open(file_solic, "w", encoding="utf-8") as f:
            json.dump(solicitacoes, f, indent=4, ensure_ascii=False)

        st.success(f"{nome} aprovado como {perfil_escolhido}")
        st.rerun()

    if col2.button(f"❌ Rejeitar {nome}", key=f"rejeitar_{nome}"):
        info["status"] = "rejeitado"

        with open(file_solic, "w", encoding="utf-8") as f:
            json.dump(solicitacoes, f, indent=4, ensure_ascii=False)

        st.warning(f"Solicitação de **{nome}** rejeitada.")
        st.rerun()
