import streamlit as st
from auth import logout

def render_header():
    col1, col2 = st.columns([6, 1])

    with col1:
        usuario = st.session_state.get("usuario", "—")
        perfil = st.session_state.get("perfil", "").upper()
        st.markdown(f"👤 **{usuario}** ({perfil})")

    with col2:
        logout()
