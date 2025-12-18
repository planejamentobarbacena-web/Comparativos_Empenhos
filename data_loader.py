# data_loader.py
import pandas as pd
from pathlib import Path
import streamlit as st

# Diretório base relativo a este arquivo
BASE_DIR = Path(__file__).parent
PASTA_DATA = BASE_DIR / "data"
PASTA_DATA.mkdir(exist_ok=True)  # cria a pasta se não existir

@st.cache_data(show_spinner="📂 Carregando empenhos...")
def load_empenhos():
    arquivos = sorted(PASTA_DATA.glob("*_empenhos.csv"))

    # Se não houver arquivos, retorna DataFrame vazio
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

    # Concatenar todos os arquivos
    df = pd.concat(dfs, ignore_index=True)

    # Criar colunas numéricas padronizadas (remover pontos, trocar vírgulas por ponto)
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
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[destino] = pd.to_numeric(df[destino], errors="coerce").fillna(0.0)
        else:
            df[destino] = 0.0

    # Compatibilidade antiga
    df["Valor"] = df["valorEmpenhadoBruto_num"]

    # Limpeza de strings
    for col in ["nomeCredor", "numRecurso", "numNaturezaEmp"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = ""

    # Garantir tipos consistentes
    df["Ano"] = df["Ano"].astype(str)
    for col in ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]:
        df[col] = pd.to_numeric(df.get(col, pd.Series([0]*len(df))), errors="coerce").fillna(0.0)

    return df
