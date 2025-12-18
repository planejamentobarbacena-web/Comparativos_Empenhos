import streamlit as st
from github_manager import upload_arquivo, excluir_arquivo

st.title("📤 Gerenciar CSVs")

# ---------------------------
# Mensagem pós-atualização
# ---------------------------
if st.session_state.get("arquivos_atualizados"):
    st.success("🔄 Arquivos atualizados com sucesso.")
    del st.session_state["arquivos_atualizados"]

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("Selecione um CSV", type=["csv"])

if arquivo is not None:
    if st.button("Enviar CSV"):
        try:
            # ✅ bytes corretos para o GitHub
            conteudo_bytes = arquivo.getvalue()

            resultado = upload_arquivo(
                conteudo_bytes,
                f"data/{arquivo.name}",
                mensagem=f"Upload {arquivo.name}"
            )

            st.success("✅ Upload realizado com sucesso!")
            st.cache_data.clear()
            st.session_state["arquivos_atualizados"] = True
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro no upload: {e}")

# =========================
# EXCLUSÃO
# =========================
st.divider()
st.subheader("🗑️ Excluir CSV")

arquivo_excluir = st.text_input("Nome do CSV (ex: 2024_empenhos.csv)")

if st.button("Excluir CSV do GitHub") and arquivo_excluir:
    try:
        caminho_repo = f"data/{arquivo_excluir.strip()}"

        excluir_arquivo(
            caminho_repo,
            mensagem=f"Remoção {arquivo_excluir}"
        )

        st.success("🗑️ Arquivo removido com sucesso!")
        st.cache_data.clear()
        st.session_state["arquivos_atualizados"] = True
        st.rerun()

    except Exception as e:
        st.error(f"❌ Erro na exclusão: {e}")
