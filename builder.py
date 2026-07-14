import pandas as pd


def construir_csv(dados: list[dict], caminho: str) -> None:
    df = pd.DataFrame(dados)
    df.columns = [col.upper().replace(" ", "_") for col in df.columns]
    df.to_csv(caminho, index=False, encoding="utf-8")
    print(f"{len(df)} registros salvos em {caminho}")
