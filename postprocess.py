import pandas as pd
import numpy as np

PREVALENCIA_ALVO = 0.30
MIN_EXCECAO = 0.15


def _fixar_prevalencia(df: pd.DataFrame, desfecho: str, alvo: float, rng) -> pd.DataFrame:
    n_alvo = round(len(df) * alvo)
    idx_sim = df.index[df[desfecho] == "SIM"].tolist()
    n_atual = len(idx_sim)

    if n_atual > n_alvo:
        flip_idx = rng.choice(idx_sim, size=n_atual - n_alvo, replace=False)
        df.loc[flip_idx, desfecho] = "NAO"
    elif n_atual < n_alvo:
        idx_nao = df.index[df[desfecho] == "NAO"].tolist()
        flip_idx = rng.choice(idx_nao, size=n_alvo - n_atual, replace=False)
        df.loc[flip_idx, desfecho] = "SIM"

    return df


def _fixar_separacao_binaria(df: pd.DataFrame, col: str, desfecho: str, min_excecao: float, rng) -> pd.DataFrame:
    valores = df[col].dropna().unique()
    if len(valores) != 2:
        return df

    for val_d in ["SIM", "NAO"]:
        sub = df[df[desfecho] == val_d]
        n_sub = len(sub)
        n_min = max(1, round(n_sub * min_excecao))

        for val_c in valores:
            n_presente = (sub[col] == val_c).sum()
            if n_presente < n_min:
                n_flip = n_min - n_presente
                outro_val = [v for v in valores if v != val_c][0]
                candidatos = df[(df[desfecho] == val_d) & (df[col] == outro_val)].index.tolist()
                n_flip = min(n_flip, len(candidatos))
                if n_flip > 0:
                    flip_idx = rng.choice(candidatos, size=n_flip, replace=False)
                    df.loc[flip_idx, col] = val_c

    return df


def postprocessar(arquivo: str, desfecho: str, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    df = pd.read_csv(arquivo)

    prev_antes = (df[desfecho] == "SIM").mean()
    df = _fixar_prevalencia(df, desfecho, PREVALENCIA_ALVO, rng)
    prev_depois = (df[desfecho] == "SIM").mean()
    print(f"  Prevalência: {prev_antes:.0%} → {prev_depois:.0%}")

    cols_cat = [c for c in df.select_dtypes(include=["object", "string"]).columns if c != desfecho]
    for col in cols_cat:
        df = _fixar_separacao_binaria(df, col, desfecho, MIN_EXCECAO, rng)

    df.to_csv(arquivo, index=False)
    print(f"  Salvo em {arquivo}")


if __name__ == "__main__":
    from config import ARQUIVO_SAIDA, DESFECHO
    print("Pós-processando dados...")
    postprocessar(ARQUIVO_SAIDA, DESFECHO)
    print("Pronto.")
