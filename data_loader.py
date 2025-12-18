import pandas as pd
from pathlib import Path
import streamlit as st


@st.cache_data(show_spinner="Carregando empenhos...")
def load_empenhos():

    pasta = Path("data")

    arquivos = sorted(
        list(pasta.glob("*_empenhos.csv")) +
        list(pasta.glob("*_empenhos.xlsx"))
    )

    if not arquivos:
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        df = None

        # =====================
        # CSV
        # =====================
        if arq.suffix.lower() == ".csv":
            encodings = ["utf-8", "utf-8-sig", "latin1"]
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
                    break
                except Exception:
                    continue

            if df is None:
                st.warning(f"Não foi possível ler {arq.name}")
                continue

        # =====================
        # XLSX
        # =====================
        elif arq.suffix.lower() == ".xlsx":
            try:
                df = pd.read_excel(arq, dtype=str)
            except Exception as e:
                st.warning(f"Erro ao ler {arq.name}: {e}")
                continue

        # =====================
        # ANO
        # =====================
        df["Ano"] = arq.stem.split("_")[0]

        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # =====================
    # CAMPOS NUMÉRICOS
    # =====================
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

    df["Valor"] = df["valorEmpenhadoBruto_num"]

    # =====================
    # LIMPEZA
    # =====================
    for col in ["nomeCredor", "numRecurso", "numNaturezaEmp"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = ""

    df["Ano"] = df["Ano"].astype(str)

    return df
