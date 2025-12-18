# data_loader.py
import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner="📂 Carregando empenhos...")
def load_empenhos_xlsx():
    """
    Carrega todos os arquivos XLSX de empenhos da pasta 'data'.
    """
    arquivos = sorted(Path("data").glob("*_empenhos.xlsx"))

    if not arquivos:
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        try:
            df = pd.read_excel(arq, dtype=str, engine="openpyxl")
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler {arq.name}: {e}")
            continue

        # Extrair o ano do nome do arquivo
        df["Ano"] = arq.stem.split("_")[0]

        # Limpeza de strings
        for col in ["nomeCredor", "numRecurso", "numNaturezaEmp"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
            else:
                df[col] = ""

        # Normalização numérica
        campos = {
            "valorEmpenhadoBruto": "valorEmpenhadoBruto_num",
            "valorEmpenhadoAnulado": "valorEmpenhadoAnulado_num",
            "valorBaixadoBruto": "valorBaixadoBruto_num"
        }

        for origem, destino in campos.items():
            if origem in df.columns:
                df[destino] = (
                    df[origem]
                    .astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                df[destino] = pd.to_numeric(df[destino], errors="coerce").fillna(0.0)
            else:
                df[destino] = 0.0

        df["Valor"] = df.get("valorEmpenhadoBruto_num", 0.0)

        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)
