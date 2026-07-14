"""Configuração compartilhada entre geração (cli.py) e análise (analise.py).

Fonte única da verdade: edite aqui o tema, as variáveis e o desfecho de cada
novo trabalho. Assim a análise bivariada roda sobre o CSV já gerado, sem
precisar chamar o Groq de novo.
"""

TEMA = "fatores de risco para câncer de colo de útero em mulheres"

# transversal → Razão de Prevalência | coorte → Risco Relativo | caso-controle → Odds Ratio
TIPO_ESTUDO = "transversal"

DESFECHO = "CANCER_COLO_UTERO"

FATORES_RISCO = {
    "HPV": "fator de risco forte — prevalência ~70% nos casos (SIM) vs ~15% nos não-casos (NAO)",
    "TABAGISMO": "fator de risco — prevalência ~50% nos casos vs ~20% nos não-casos",
    "NUM_PARCEIROS": "fator de risco — média ~7 nos casos vs ~2 nos não-casos",
    "EXAME_PREVENTIVO": "fator protetor — prevalência ~30% nos casos vs ~75% nos não-casos",
    "USO_PRESERVATIVO": "fator protetor — prevalência ~20% nos casos vs ~60% nos não-casos",
}

VARIAVEIS = {
    "IDADE": "inteiro entre 18 e 70",
    "ESCOLARIDADE": "um de: FUND_INCOMPLETO, FUND_COMPLETO, MEDIO_INCOMPLETO, MEDIO_COMPLETO, SUP_INCOMPLETO, SUP_COMPLETO",
    "ESTADO_CIVIL": "um de: SOLTEIRA, CASADA, DIVORCIADA, VIUVA",
    "RENDA_FAMILIAR": "decimal em reais entre 500.00 e 15000.00",
    "CANCER_COLO_UTERO": "SIM ou NAO (diagnóstico confirmado)",
    "NUM_PARCEIROS": "inteiro entre 1 e 15 (parceiros sexuais ao longo da vida)",
    "IDADE_PRIMEIRA_RELACAO": "inteiro entre 12 e 30",
    "IDADE_PRIMEIRA_MENSTRUACAO": "inteiro entre 9 e 16",
    "NUM_GESTACOES": "inteiro entre 0 e 10",
    "USO_PRESERVATIVO": "SIM ou NAO",
    "TABAGISMO": "SIM ou NAO",
    "CONTRACEPTIVO_ORAL": "SIM ou NAO",
    "EXAME_PREVENTIVO": "SIM ou NAO (realiza anualmente)",
    "ACOMPANHAMENTO_GINECOLOGICO": "SIM ou NAO",
    "SERVICO_SAUDE": "um de: SUS, PLANO_SAUDE, PARTICULAR",
    "HPV": "SIM ou NAO (histórico de infecção por HPV)",
}

N = 60

ARQUIVO_SAIDA = "dados.csv"
