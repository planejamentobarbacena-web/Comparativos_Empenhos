# data_loader.py
import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner="📂 Carregando empenhos...")
def load_empenhos():
    """
    Carrega todos os arquivos CSV de empenhos da pasta 'data', 
    tentando diferentes encodings para evitar problemas de acentuação.
    """
    arquivos = sorted(Path("data").glob("*_empenhos.csv"))

    if not arquivos:
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        encodings = ["utf-8", "utf-8-sig", "latin1"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(
                    arq,
                    sep=";",
                    dtype=str,
                    encoding=enc,
                    engine="python",
                    on_bad_lines="skip"
                )
                break  # leu corretamente
            except Exception:
                continue
        
        if df is None:
            st.warning(f"⚠️ Não foi possível ler {arq.name}.")
            continue

        # Corrigir caracteres estranhos (ex: Ã)
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).apply(lambda x: x.encode('utf-8', errors='replace').decode('utf-8'))

        # Extrair o ano do nome do arquivo
        df["Ano"] = arq.stem.split("_")[0]
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

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
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
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
@st.cache_data(show_spinner="📂 Carregando empenhos (CSV + XLSX)...")
def load_empenhos_flex():
    import pandas as pd
    from pathlib import Path

    arquivos_csv = sorted(Path("data").glob("*_empenhos.csv"))
    arquivos_xlsx = sorted(Path("data").glob("*_empenhos.xlsx"))

    arquivos = arquivos_csv + arquivos_xlsx

    if not arquivos:
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        try:
            if arq.suffix == ".csv":
                df = pd.read_csv(
                    arq,
                    sep=";",
                    dtype=str,
                    encoding="latin1",
                    engine="python",
                    on_bad_lines="skip"
                )
            else:
                df = pd.read_excel(arq, dtype=str)
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler {arq.name}: {e}")
            continue

        df["Ano"] = arq.stem.split("_")[0]
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

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

    df["Valor"] = df["valorEmpenhadoBruto_num"]

    for col in ["nomeCredor", "numRecurso", "numNaturezaEmp"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = ""

    df["Ano"] = df["Ano"].astype(str)

    return df
