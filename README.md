# epi-generator

CLI que gera **dados sintéticos coerentes para estudos epidemiológicos** e roda
uma **análise bivariada automática** sobre eles.

## O problema

Praticar análise epidemiológica — medidas de associação, testes de hipótese —
exige um conjunto de dados. Dados reais de pacientes são sensíveis e difíceis de
obter; dados inventados na mão costumam ser incoerentes: os fatores de risco não
se correlacionam com o desfecho como o mundo real correlaciona, ou correlacionam
_demais_ (separação perfeita), o que denuncia o dado como artificial e produz
p-valores irreais.

## A solução

Uma CLI que gera um dataset sintético a partir de uma configuração declarativa
(tema, variáveis e seus domínios, desfecho, fatores de risco esperados). Usa um
LLM para introduzir correlações realistas **com variação individual** — nem todo
caso positivo tem o fator, alguns negativos têm. Exporta um CSV limpo, com
colunas compatíveis com ferramentas de análise como o Epi-Info, e — num passo
desacoplado — roda uma análise bivariada completa gerando um relatório Markdown.

```
config.py  (tema, variáveis, desfecho, fatores de risco, N)
    │
    ├── cli.py ──▶ generator.py (Groq/LLM → JSON) ──▶ builder.py (pandas → CSV)
    │                                                        │
    │                                                    dados.csv
    │
    └── analise.py (lê o CSV, não chama o LLM) ──▶ analise_bivariada.md
```

Geração e análise são desacopladas de propósito: a geração gasta tokens do LLM;
a análise roda quantas vezes quiser sobre o CSV já gerado, sem custo.

## Como funciona

- **`generator.py`** — monta o prompt e chama a Groq API (Llama 3.3). Gera em
  lotes, extrai o array JSON por regex e descarta registros com colunas
  faltantes. O prompt pede diferença de frequência entre grupos _com variação
  individual_, evitando a separação perfeita que produziria p ≈ 0 artificial.
- **`builder.py`** — normaliza os nomes de coluna (maiúsculo, sem acento nem
  espaço) e exporta o CSV via pandas.
- **`analise.py`** — para cada variável independente contra o desfecho:
  - **qualitativas** → tabela de contingência, medida de associação
    (RP / RR / OR conforme o tipo de estudo) com IC 95% e valor de p
    (Qui-quadrado, ou Exato de Fisher quando alguma célula esperada < 5);
  - **quantitativas** → média ± desvio-padrão por grupo e p de Mann-Whitney
    (ou Kruskal-Wallis para 3+ grupos).

## Instalação

Requer Python 3.13+ e [uv](https://docs.astral.sh/uv/).

```bash
git clone <url-do-repo>
cd epi-generator
uv sync
```

Crie um `.env` com sua chave da Groq (gratuita em
[console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=sua_chave_aqui
```

## Uso

1. Edite `config.py`: `TEMA`, `VARIAVEIS` (nome → domínio), `DESFECHO`,
   `FATORES_RISCO`, `TIPO_ESTUDO` e `N`.
2. Gere os dados:
   ```bash
   uv run --env-file .env python cli.py
   ```
3. Rode a análise sobre o CSV gerado:
   ```bash
   uv run python analise.py
   ```

Saídas: `dados.csv` (o dataset) e `analise_bivariada.md` (o relatório).

> Em questionários com muitos campos, ajuste `TAMANHO_LOTE` em `generator.py`
> para não estourar o limite de tokens de saída do modelo.

## Stack

Python · Groq API (Llama 3.3) · pandas · scipy
