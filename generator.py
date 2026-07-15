import os
import json
import re
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

TAMANHO_LOTE = 5


def _extrair_json(texto: str) -> str:
    match = re.search(r"\[.*\]", texto, re.DOTALL)
    if not match:
        raise ValueError(f"Nenhum array JSON encontrado na resposta:\n{texto}")
    return match.group()


def _gerar_lote(
    tema: str,
    variaveis: dict,
    n: int,
    tipo_estudo: str = "",
    desfecho: str = "",
    fatores_risco: dict = None,
) -> list[dict]:
    variaveis_formatadas = "\n".join(
        f"- {nome}: {descricao}" for nome, descricao in variaveis.items()
    )

    secao_correlacoes = ""
    if desfecho and fatores_risco:
        itens = "\n".join(f"  - {var}: {desc}" for var, desc in fatores_risco.items())
        secao_correlacoes = f"""
Distribuição epidemiológica esperada:
- Variável de desfecho: {desfecho}
- Tipo de estudo: {tipo_estudo}
- Prevalência alvo de {desfecho} = SIM: entre 25% e 35% dos registros do lote.
- Os fatores abaixo devem apresentar diferença de frequência entre os grupos, MAS com variação individual — ou seja, nem todos os casos SIM terão o fator presente, e alguns casos NAO podem ter o fator. Dados reais têm exceções:
{itens}
"""

    prompt = f"""Você é um gerador de dados sintéticos para estudos epidemiológicos.

Gere {n} registros fictícios sobre o tema: {tema}.

Variáveis e domínios:
{variaveis_formatadas}
{secao_correlacoes}
Regras:
- Retorne APENAS um array JSON válido, sem texto antes ou depois.
- Cada elemento do array é um objeto com exatamente as chaves listadas acima.
- Nomes das chaves: sem acento, maiúsculo, sem espaço.

Exemplo de formato esperado (com 2 registros):
[{{"VARIAVEL1": valor1, "VARIAVEL2": valor2}}, {{"VARIAVEL1": valor3, "VARIAVEL2": valor4}}]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    texto = response.choices[0].message.content
    return json.loads(_extrair_json(texto))


def _filtrar_validos(registros: list[dict], colunas_esperadas: set) -> list[dict]:
    validos = []
    for registro in registros:
        if colunas_esperadas.issubset(registro.keys()):
            validos.append(registro)
        else:
            faltando = colunas_esperadas - registro.keys()
            print(f"  Registro descartado — colunas ausentes: {faltando}")
    return validos


def _salvar_checkpoint(path: str, registros: list[dict], tema: str, n: int):
    with open(path, "w") as f:
        json.dump({"tema": tema, "n": n, "registros": registros}, f)


def _carregar_checkpoint(path: str, tema: str, n: int) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        dados = json.load(f)
    if dados.get("tema") != tema or dados.get("n") != n:
        print("  Checkpoint inválido (tema ou N diferente) — ignorando.")
        return []
    registros = dados.get("registros", [])
    if registros:
        print(f"  Checkpoint encontrado — retomando de {len(registros)}/{n} registros.")
    return registros


def gerar_dados(
    tema: str,
    variaveis: dict,
    n: int,
    tipo_estudo: str = "",
    desfecho: str = "",
    fatores_risco: dict = None,
    checkpoint_path: str = "checkpoint.json",
) -> list[dict]:
    colunas_esperadas = set(variaveis.keys())
    resultado = _carregar_checkpoint(checkpoint_path, tema, n)

    while len(resultado) < n:
        faltam = n - len(resultado)
        lote = min(faltam, TAMANHO_LOTE)
        print(f"  Gerando lote de {lote} registros... ({len(resultado)}/{n} prontos)")
        novos = _gerar_lote(tema, variaveis, lote, tipo_estudo, desfecho, fatores_risco)
        resultado += _filtrar_validos(novos, colunas_esperadas)
        _salvar_checkpoint(checkpoint_path, resultado, tema, n)

    os.remove(checkpoint_path)
    return resultado
