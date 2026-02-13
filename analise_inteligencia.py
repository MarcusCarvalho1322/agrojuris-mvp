import pandas as pd
from datetime import datetime
import os

# CONFIG
BASE_PATH = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie"
INPUT_FILE = "LISTA_FINAL_ATAQUE_COMERCIAL_2026_DIAMANTE_ENRIQUECIDA_OSINT.csv"
OUTPUT_FILE = "LISTA_DIAMANTE_MATRIZ_TESES_2026.csv"

# DATA REFERENCE (Jan 2026)
CURR_DATE = datetime(2026, 1, 12)

def analyze_lead_strategy(row):
    """
    Define a melhor tese jurídica com base nos dados do auto.
    """
    try:
        dt_str = str(row['DAT_HORA_AUTO_INFRACAO'])[:10] # YYYY-MM-DD
        data_infracao = datetime.strptime(dt_str, "%Y-%m-%d")
        days_diff = (CURR_DATE - data_infracao).days
    except:
        data_infracao = None
        days_diff = 0
    
    desc = str(row['DES_INFRACAO']).upper()
    status = str(row['DES_STATUS_FORMULARIO']).upper()
    val = float(row['VALOR_MULTA']) if pd.notnull(row['VALOR_MULTA']) else 0
    
    teses = []
    
    # --- ANÁLISE DE NULIDADES (A PEDIDO) ---
    # TESE 1: NULIDADE POR SATÉLITE (GEORREFERENCIAMENTO)
    # Se for infração contra FLORA, 90% é satélite.
    if "FLORA" in desc or "DESMAT" in desc or "VEGET" in desc or "DESTRUIR" in desc:
        teses.append("TESE 1: NULIDADE (ERRO SATÉLITE)")
        
    # --- ANÁLISE CRONOLÓGICA ---
    # TESE 4: PRESCRIÇÃO INTERCORRENTE
    # Processos com mais de 3 anos (1095 dias) potencialmente parados
    if days_diff > 1095: 
        teses.append("TESE 4: PRESCRIÇÃO (PROC. PARADO > 3 ANOS)")
        
    # TESE 3: CONVERSÃO DE MULTA (CRA)
    # Multas recentes (< 1 ano) ainda na fase de defesa/alegações
    if days_diff < 365 and "LAVRADO" in status:
         teses.append("TESE 3: CONVERSÃO IMEDIATA (60% OFF)")

    # --- ANÁLISE ECONÔMICA ---
    # TESE 5: CONFISCO / DESPROPORCIONALIDADE
    if val > 5000000: # Acima de 5 Milhões
        teses.append("TESE 5: DESPROPORCIONALIDADE (CONFISCO)")
    
    # CLASSIFICAÇÃO FINAL
    primary = teses[0] if teses else "ANÁLISE DE MÉRITO GENÉRICA"
    secondary = teses[1] if len(teses) > 1 else ""
    
    # PRIORIZAÇÃO DE "NULIDADE" SE FOR FLORA RECENTE
    if "NULIDADE" in primary and days_diff < 1095:
        # Se for recente e Flora, Nulidade é muito forte.
        pass
    elif "PRESCRIÇÃO" in primary:
        # Se for antigo, Prescrição ganha de Nulidade na facilidade
        pass
        
    return pd.Series([primary, secondary, days_diff])

print(">>> INICIANDO MATRIZ DE APLICAÇÃO DE TESES JURÍDICAS...")
full_path_in = os.path.join(BASE_PATH, INPUT_FILE)
full_path_out = os.path.join(BASE_PATH, OUTPUT_FILE)

if os.path.exists(full_path_in):
    df = pd.read_csv(full_path_in, sep=';', encoding='utf-8-sig')
    
    # Aplica a Inteligência Jurídica
    df[['TESE_PRIMARIA', 'TESE_SECUNDARIA', 'DIAS_DECORRIDOS']] = df.apply(analyze_lead_strategy, axis=1)
    
    # Reordena colunas para facilitar leitura comercial
    cols = ['NOME_INFRATOR', 'VALOR_MULTA', 'TESE_PRIMARIA', 'TESE_SECUNDARIA', 'LINK_RAPIDO_CONTATO', 'MUNICIPIO', 'DAT_HORA_AUTO_INFRACAO']
    # Add whatever else remains
    other_cols = [c for c in df.columns if c not in cols]
    df_final = df[cols + other_cols]
    
    df_final.to_csv(full_path_out, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\n[SUCESSO] Relatório Gerado: {OUTPUT_FILE}")
    
    # GERA RESUMO NO CONSOLE
    print("\n--- RESUMO ESTRATÉGICO ---")
    print(df_final['TESE_PRIMARIA'].value_counts())

    print("\n--- RECORTE: NULIDADES (ERRO SATÉLITE) ---")
    nulidade_count = len(df_final[df_final['TESE_PRIMARIA'].str.contains("NULIDADE")])
    print(f"Total de Leads para atacar com Tese de Nulidade: {nulidade_count}")

else:
    print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
