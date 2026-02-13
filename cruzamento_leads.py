import pandas as pd
import glob
import os

# CONFIG
PATH_IBAMA = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\dados_ibama\auto_infracao"
PATH_BC = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\dados_bc"
OUTPUT_FILE = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\LISTA_FINAL_ATAQUE_COMERCIAL_2026.csv"

# 1. CARREGAR DADOS DO IBAMA (NOMES)
print(">>> Carregando Dados do IBAMA 2022-2025...")
ibama_files = glob.glob(os.path.join(PATH_IBAMA, "auto_infracao_ano_202[2-5].csv"))
dfs_ibama = []

for f in ibama_files:
    try:
        # IBAMA uses ; separator and latin-1 usually
        df = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
        # Select relevant columns - ENRICHED FOR SALES AND AUTOMATION
        cols = [
            'SEQ_AUTO_INFRACAO', 'NOME_INFRATOR', 'CPF_CNPJ_INFRATOR', 'MUNICIPIO', 'UF', 
            'VAL_AUTO_INFRACAO', 'DAT_HORA_AUTO_INFRACAO', 'DES_INFRACAO', 
            'DES_STATUS_FORMULARIO', 'SIT_CANCELADO', 'DES_LOCAL_INFRACAO', 'TIPO_INFRACAO',
            'NUM_LATITUDE_AUTO', 'NUM_LONGITUDE_AUTO'
        ]
        # Normalize columns if needed (sometimes verify header)
        df.columns = [c.upper().strip() for c in df.columns]
        
        # Check if columns exist
        available_cols = [c for c in cols if c in df.columns]
        df = df[available_cols]
        dfs_ibama.append(df)
        print(f"   > Carregado: {os.path.basename(f)} ({len(df)} registros)")
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")

if not dfs_ibama:
    print("ERRO: Nenhum arquivo IBAMA carregado.")
    exit()

df_ibama_full = pd.concat(dfs_ibama, ignore_index=True)

# Limpeza e Tipagem
# CORRIGIDO: Usando VAL_AUTO_INFRACAO
df_ibama_full['VALOR_MULTA'] = pd.to_numeric(df_ibama_full['VAL_AUTO_INFRACAO'].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
df_ibama_full['MUNICIPIO'] = df_ibama_full['MUNICIPIO'].astype(str).str.upper()

# FILTRO 1: APENAS MULTAS RELEVANTES (> R$ 1k) E ATIVAS (NÃO CANCELADAS)
# Filter status if column exists
if 'SIT_CANCELADO' in df_ibama_full.columns:
    df_leads = df_ibama_full[
        (df_ibama_full['VALOR_MULTA'] >= 1000) & 
        (df_ibama_full['SIT_CANCELADO'] != 'S')
    ].copy()
else:
    df_leads = df_ibama_full[df_ibama_full['VALOR_MULTA'] >= 1000].copy()

print(f">>> Leads Qualificados (AMPLA CAPTURA >1k): {len(df_leads)}")
print(f">>> Total de Multas Relevantes (>1k): {len(df_leads)}")


# 2. CARREGAR DADOS DO CRÉDITO (CIDADES RICAS)
print("\n>>> Carregando Dados do SICOR/BACEN (Matriz de Crédito)...")
bc_pattern = os.path.join(PATH_BC, "SICOR_CONTRATOS_MUNICIPIO_202*.gz")
print(f"DEBUG: Buscando padrão: {bc_pattern}")
bc_files = glob.glob(bc_pattern)
print(f"DEBUG: Arquivos encontrados: {len(bc_files)}")
dfs_bc = []

for f in bc_files:
    try:
        # SICOR public CSVs often use ; and latin-1
        df = pd.read_csv(f, sep=';', encoding='latin-1', compression='gzip', low_memory=False)
        cols_bc = ['nome_municipio', 'valor_contrato'] # Check if column names match
        
        # Standardize columns to upper
        df.columns = [c.upper().strip() for c in df.columns]
        
        # DEBUG Columns
        if not dfs_bc:
            print(f"DEBUG SICOR COLS: {list(df.columns)}")

        # SICOR 2024+ Columns Logic
        val_columns = ['VLCUSTEIO', 'VLINVESTIMENTO', 'VLCOMERCIALIZACAO', 'VLINDUSTRIALIZACAO']
        existing_val_cols = [c for c in val_columns if c in df.columns]
        
        mun_col = 'MUNICIPIO'
        
        if mun_col in df.columns and existing_val_cols:
            df = df[[mun_col] + existing_val_cols].copy()
            # Convert to numeric
            for c in existing_val_cols:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            
            # Sum total credit
            df['VALOR_CONTRATO'] = df[existing_val_cols].sum(axis=1)
            
            df = df[[mun_col, 'VALOR_CONTRATO']] # Keep only final
            dfs_bc.append(df)
            print(f"   > Carregado: {os.path.basename(f)} (Total: {df['VALOR_CONTRATO'].sum():,.2f})")
        else:
            print(f"SKIP {f}: Colunas esperadas não encontradas.")
    except Exception as e:
        print(f"Erro BC {f}: {e}")

df_bc_full = pd.concat(dfs_bc, ignore_index=True)
df_bc_city = df_bc_full.groupby('MUNICIPIO')['VALOR_CONTRATO'].sum().reset_index()
df_bc_city['MUNICIPIO'] = df_bc_city['MUNICIPIO'].str.upper()
df_bc_city.rename(columns={'VALOR_CONTRATO': 'VOLUME_CREDITO_CIDADE', 'MUNICIPIO': 'NOME_MUNICIPIO'}, inplace=True)

print(f">>> Cidades Mapeadas com Crédito: {len(df_bc_city)}")

# 3. CRUZAMENTO (LISTA DE OURO)
print("\n>>> Cruzando Dados (LEADS v. DINHEIRO)...")

# Join on Name of Municipality
# Note: Cleaning names is usually required (remove accents), but let's try direct first for MVP
# Using unidecode would be better, but assuming data sources use standard caps
df_final = pd.merge(df_leads, df_bc_city, left_on='MUNICIPIO', right_on='NOME_MUNICIPIO', how='left')

# Fill NaN credit with 0 (City has no significant credit)
df_final['VOLUME_CREDITO_CIDADE'] = df_final['VOLUME_CREDITO_CIDADE'].fillna(0)

# SCORING DE OPORTUNIDADE
# Score = (Multa Normalizada * 0.3) + (Credito Cidade Normalizado * 0.7)
# But simple Filters are better for actionable lists

# Filter: Must be in a city with at least R$ 100 Million in credit (Otherwise bank branch is weak)
df_gold = df_final[df_final['VOLUME_CREDITO_CIDADE'] > 100_000_000].copy()

# Sort by Fine Value (Highest Pain)
df_gold = df_gold.sort_values(by='VALOR_MULTA', ascending=False)

# Select Output Columns - EXTENDED FOR SALES AND AUTOMATION
out_cols = [
    'NOME_INFRATOR', 'CPF_CNPJ_INFRATOR', 'MUNICIPIO', 'UF', 
    'VALOR_MULTA', 'DES_INFRACAO', 'VOLUME_CREDITO_CIDADE', 
    'DES_STATUS_FORMULARIO', 'DES_LOCAL_INFRACAO', 'DAT_HORA_AUTO_INFRACAO',
    'NUM_LATITUDE_AUTO', 'NUM_LONGITUDE_AUTO'
]
# Ensure columns exist before selecting
final_cols = [c for c in out_cols if c in df_gold.columns]

df_export = df_gold[final_cols]

# SEGMENTAÇÃO
print("\n>>> SEGMENTANDO LISTAS (DIAMANTE, OURO, PRATA)...")

# DIAMANTE (> 500k)
df_diamante = df_export[df_export['VALOR_MULTA'] >= 500000]
file_diamante = OUTPUT_FILE.replace(".csv", "_DIAMANTE.csv")
df_diamante.to_csv(file_diamante, index=False, sep=';', encoding='utf-8-sig')
print(f"   > LEADS DIAMANTE (>500k): {len(df_diamante)} registros -> {file_diamante}")

# OURO (50k - 500k)
df_ouro = df_export[(df_export['VALOR_MULTA'] >= 50000) & (df_export['VALOR_MULTA'] < 500000)]
file_ouro = OUTPUT_FILE.replace(".csv", "_OURO.csv")
df_ouro.to_csv(file_ouro, index=False, sep=';', encoding='utf-8-sig')
print(f"   > LEADS OURO (50k-500k): {len(df_ouro)} registros -> {file_ouro}")

# PRATA (< 50k)
df_prata = df_export[df_export['VALOR_MULTA'] < 50000]
file_prata = OUTPUT_FILE.replace(".csv", "_PRATA.csv")
df_prata.to_csv(file_prata, index=False, sep=';', encoding='utf-8-sig')
print(f"   > LEADS PRATA (<50k): {len(df_prata)} registros -> {file_prata}")

print(f"\n[SUCESSO] 3 LISTAS DE ATAQUE GERADAS NA PASTA!")
