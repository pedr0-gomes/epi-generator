from generator import gerar_dados
from builder import construir_csv
from postprocess import postprocessar
from config import TEMA, TIPO_ESTUDO, DESFECHO, FATORES_RISCO, VARIAVEIS, N, ARQUIVO_SAIDA

if __name__ == "__main__":
    print(f"Gerando {N} registros sobre: {TEMA} ({TIPO_ESTUDO})")
    dados = gerar_dados(TEMA, VARIAVEIS, N, TIPO_ESTUDO, DESFECHO, FATORES_RISCO)
    construir_csv(dados, ARQUIVO_SAIDA)
    print("Pós-processando...")
    postprocessar(ARQUIVO_SAIDA, DESFECHO)
