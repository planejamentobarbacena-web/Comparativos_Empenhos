# data_loader.py
import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner="📂 Carregando empenhos...")
def load_empenhos():
    arquivos = sorted(Path("data").glob("*_empenhos.csv"))

    if not arquivos:
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        try:
            df = pd.read_csv(
                arq,
                sep=";",
                dtype=str,
                encoding="utf-8",
                engine="python",
                on_bad_lines="skip"
            )
        except UnicodeDecodeError:
            df = pd.read_csv(
                arq,
                sep=";",
                dtype=str,
                encoding="latin1",
                engine="python",
                on_bad_lines="skip"
            )

        # Extrair o ano do nome do arquivo
        df["Ano"] = arq.stem.split("_")[0]
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # Criar colunas numéricas padronizadas (sem espaços, vírgulas para ponto)
    mapping = {
        "valorEmpenhadoBruto": "valorEmpenhadoBruto_num",
        "valorEmpenhadoAnulado": "valorEmpenhadoAnulado_num",
        "valorBaixadoBruto": "valorBaixadoBruto_num"
    }

    for origem, destino in mapping.items():
        if origem in df.columns:
            df[destino] = (
                df[origem]
                .astype(str)
                .str.replace(".", "", regex=False)   # remove separador de milhar
                .str.replace(",", ".", regex=False)  # transforma vírgula em ponto
            )
            df[destino] = pd.to_numeric(df[destino], errors="coerce").fillna(0.0)
        else:
            df[destino] = 0.0

    # Mantém compatibilidade antiga
    df["Valor"] = df["valorEmpenhadoBruto_num"]

    # Limpeza de strings para evitar problemas em filtros
    for col in ["nomeCredor", "numRecurso", "numNaturezaEmp"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = ""

    # Garantir tipos consistentes
    df["Ano"] = df["Ano"].astype(str)
    for col in ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    return df
