"""Análise bivariada: cada variável independente vs o desfecho.

Qualitativas → tabela de contingência, medida de associação (RP/RR/OR conforme
o tipo de estudo) com IC 95% e valor de p (Qui-quadrado, ou Exato de Fisher
quando alguma célula esperada < 5).
Quantitativas → média ± desvio padrão por grupo do desfecho e p de Mann-Whitney.

Roda sobre o CSV já gerado (não chama o Groq). Uso: python analise.py
"""

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, chi2_contingency, mannwhitneyu, kruskal

# tipo de estudo → (nome da medida, forma de cálculo)
MEDIDA_POR_ESTUDO = {
    "transversal": ("Razão de Prevalência (RP)", "rr"),
    "coorte": ("Risco Relativo (RR)", "rr"),
    "caso-controle": ("Odds Ratio (OR)", "or"),
}


def _classificar(df: pd.DataFrame, desfecho: str) -> tuple[list, list]:
    """Numérico → quantitativa; texto → qualitativa. Exclui o desfecho."""
    quant, qual = [], []
    for col in df.columns:
        if col == desfecho:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            quant.append(col)
        else:
            qual.append(col)
    return quant, qual


def _rotulos_desfecho(serie: pd.Series) -> tuple[str, str]:
    """Devolve (positivo, negativo). Prefere SIM/NAO; senão ordena e usa o maior como positivo."""
    cats = set(serie.dropna().unique())
    if {"SIM", "NAO"}.issubset(cats):
        return "SIM", "NAO"
    ordenado = sorted(cats)
    return ordenado[-1], ordenado[0]


def _medida_associacao(a, b, c, d, tipo_estudo):
    """a,b,c,d = expostos-positivos, expostos-negativos, ref-positivos, ref-negativos.

    Aplica correção de continuidade (+0,5) se alguma célula for zero, para não
    dividir por zero no cálculo do IC.
    """
    corrigido = 0 in (a, b, c, d)
    if corrigido:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5

    _, forma = MEDIDA_POR_ESTUDO.get(tipo_estudo, MEDIDA_POR_ESTUDO["transversal"])
    if forma == "or":
        ponto = (a * d) / (b * c)
        se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    else:  # RR / RP
        ponto = (a / (a + b)) / (c / (c + d))
        se = np.sqrt(b / (a * (a + b)) + d / (c * (c + d)))

    ic_baixo = np.exp(np.log(ponto) - 1.96 * se)
    ic_alto = np.exp(np.log(ponto) + 1.96 * se)
    return ponto, ic_baixo, ic_alto, corrigido


def _teste_contingencia(tabela: np.ndarray) -> tuple[float, str]:
    """Qui-quadrado por padrão; Fisher se alguma célula esperada < 5 (só 2x2)."""
    _, p_chi2, _, esperadas = chi2_contingency(tabela)
    if (esperadas < 5).any():
        if tabela.shape == (2, 2):
            _, p = fisher_exact(tabela)
            return p, "Exato de Fisher"
        return p_chi2, "Qui-quadrado (atenção: células esperadas < 5)"
    return p_chi2, "Qui-quadrado"


def _analisar_qualitativa(df, var, desfecho, pos, neg, tipo_estudo) -> str:
    tab = pd.crosstab(df[var], df[desfecho])
    for col in (pos, neg):  # garante ambas as colunas do desfecho
        if col not in tab.columns:
            tab[col] = 0
    tab = tab[[pos, neg]]

    linhas = [f"### {var}", "", f"| {var} | {pos} (n, col%) | {neg} (n, col%) |", "|---|---|---|"]
    total_pos, total_neg = tab[pos].sum(), tab[neg].sum()
    for cat, row in tab.iterrows():
        pp = 100 * row[pos] / total_pos if total_pos else 0
        pn = 100 * row[neg] / total_neg if total_neg else 0
        linhas.append(f"| {cat} | {row[pos]} ({pp:.1f}%) | {row[neg]} ({pn:.1f}%) |")

    p, teste = _teste_contingencia(tab.values)

    if tab.shape[0] == 2:  # dicotômica → medida de associação
        cats = list(tab.index)
        exp = "SIM" if "SIM" in cats else sorted(cats)[-1]
        ref = [x for x in cats if x != exp][0]
        a, b = tab.loc[exp, pos], tab.loc[exp, neg]
        c, d = tab.loc[ref, pos], tab.loc[ref, neg]
        ponto, ic_b, ic_a, corr = _medida_associacao(a, b, c, d, tipo_estudo)
        nome_medida = MEDIDA_POR_ESTUDO.get(tipo_estudo, MEDIDA_POR_ESTUDO["transversal"])[0]
        nota_corr = " *(células zeradas → correção +0,5)*" if corr else ""
        linhas += [
            "",
            f"- **{nome_medida}** (exposto = {exp}): {ponto:.4f} — IC 95% [{ic_b:.4f} – {ic_a:.4f}]{nota_corr}",
            f"- **p = {p:.4f}** ({teste})",
        ]
    else:  # policotômica → sem medida única
        linhas += [
            "",
            f"- Variável policotômica ({tab.shape[0]} categorias) — medida de associação única não se aplica.",
            f"- **p = {p:.4f}** ({teste})",
        ]

    linhas.append("")
    return "\n".join(linhas)


def _analisar_quantitativa(df, var, desfecho, ordem) -> list:
    grupos = [df[df[desfecho] == lvl][var].dropna() for lvl in ordem]
    linha = f"| {var} |"
    for g in grupos:
        linha += f" {g.mean():.2f} ± {g.std():.2f} (n={len(g)}) |"

    if len(grupos) == 2:
        _, p = mannwhitneyu(grupos[0], grupos[1], alternative="two-sided")
        teste = "Mann-Whitney"
    else:
        _, p = kruskal(*grupos)
        teste = "Kruskal-Wallis"
    linha += f" {p:.4f} ({teste}) |"
    return linha


def analisar_bivariada(df: pd.DataFrame, desfecho: str, tipo_estudo: str) -> str:
    quant, qual = _classificar(df, desfecho)
    pos, neg = _rotulos_desfecho(df[desfecho])
    ordem = [pos, neg]

    partes = [
        f"# Análise bivariada — desfecho: {desfecho}",
        f"\nTipo de estudo: **{tipo_estudo}** | "
        f"Medida: **{MEDIDA_POR_ESTUDO.get(tipo_estudo, MEDIDA_POR_ESTUDO['transversal'])[0]}**",
        f"\nN = {len(df)} | {desfecho} = {pos}: {(df[desfecho] == pos).sum()} "
        f"({100 * (df[desfecho] == pos).mean():.1f}%)",
        "\n## Variáveis qualitativas\n",
    ]
    for var in qual:
        partes.append(_analisar_qualitativa(df, var, desfecho, pos, neg, tipo_estudo))

    partes.append("## Variáveis quantitativas\n")
    cab = f"| Variável | {pos} (média ± DP) | {neg} (média ± DP) | p (teste) |"
    partes += [cab, "|---|---|---|---|"]
    for var in quant:
        partes.append(_analisar_quantitativa(df, var, desfecho, ordem))
    partes.append("")

    return "\n".join(partes)


if __name__ == "__main__":
    from config import DESFECHO, TIPO_ESTUDO, ARQUIVO_SAIDA

    df = pd.read_csv(ARQUIVO_SAIDA)
    relatorio = analisar_bivariada(df, DESFECHO, TIPO_ESTUDO)

    saida = "analise_bivariada.md"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(relatorio)
    print(f"Análise bivariada salva em {saida}")
