import os
import requests
import zipfile
import pandas as pd
import io
from datetime import datetime

# URLs
URL_AUTOS = "https://dadosabertos.ibama.gov.br/dados/SIFISC/auto_infracao/auto_infracao/auto_infracao_csv.zip"
URL_EMBARGOS = "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo_csv.zip"

WEB_ROOT = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie"
DATA_DIR = os.path.join(WEB_ROOT, "dados_ibama_analysis")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def download_and_extract(url, name):
    print(f"Baixando {name}...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(DATA_DIR)
        print(f"{name} extraído com sucesso.")
        return z.namelist()
    except Exception as e:
        print(f"Erro ao baixar {name}: {e}")
        return []

# Download data
files_autos = download_and_extract(URL_AUTOS, "Autos de Infracao")
files_embargos = download_and_extract(URL_EMBARGOS, "Termos de Embargo")

# Find the CSV files (assuming one per zip or predictable names)
# Usually the zip contains one csv file
csv_autos = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and 'auto_infracao' in f]
csv_embargos = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and 'termo_embargo' in f]

if not csv_autos or not csv_embargos:
    print("Arquivos CSV não encontrados após extração.")
    # Check what files are there
    print("Arquivos na pasta:", os.listdir(DATA_DIR))
    exit()

csv_auto_path = os.path.join(DATA_DIR, csv_autos[0])
csv_embargo_path = os.path.join(DATA_DIR, csv_embargos[0])

print(f"Analisando Autos: {csv_auto_path}")
print(f"Analisando Embargos: {csv_embargo_path}")

# Analysis Configuration
YEARS = [2022, 2023, 2024, 2025, 2026]

def analyze_autos(file_path):
    print("\n--- ANÁLISE DE AUTOS DE INFRAÇÃO ---")
    # Read manually to handle potential bad lines or encoding
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8', on_bad_lines='skip', low_memory=False)
    except:
         df = pd.read_csv(file_path, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
    
    # DAT_HORA_AUTO_INFRACAO format usually dd/mm/yyyy
    df['DATA'] = pd.to_datetime(df['DAT_HORA_AUTO_INFRACAO'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df['ANO'] = df['DATA'].dt.year
    
    df_filtered = df[df['ANO'].isin(YEARS)]
    
    # Convert value to float (replace comma with dot)
    df_filtered['VAL_AUTO_INFRACAO'] = df_filtered['VAL_AUTO_INFRACAO'].astype(str).str.replace(',', '.').astype(float)
    
    print(f"Total registros filtrados (2022-2026): {len(df_filtered)}")
    
    summary = df_filtered.groupby('ANO').agg({
        'SEQ_AUTO_INFRACAO': 'count',
        'VAL_AUTO_INFRACAO': 'sum'
    }).rename(columns={'SEQ_AUTO_INFRACAO': 'Qtd Autos', 'VAL_AUTO_INFRACAO': 'Valor Total (R$)'})
    
    print(summary)
    
    print("\nTop 5 Estados por Ano (Qtd Autos):")
    for year in YEARS:
        df_year = df_filtered[df_filtered['ANO'] == year]
        if not df_year.empty:
            print(f"\n{year}:")
            print(df_year['UF'].value_counts().head(5))

    print("\nTop 5 Infrações (DES_INFRACAO) mais comuns no período:")
    try:
        print(df_filtered['DES_INFRACAO'].value_counts().head(5))
    except KeyError:
        print("Coluna DES_INFRACAO não encontrada ou vazia")

def analyze_embargos(file_path):
    print("\n--- ANÁLISE DE TERMOS DE EMBARGO ---")
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8', on_bad_lines='skip', low_memory=False)
    except:
        df = pd.read_csv(file_path, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)

    # DAT_EMBARGO
    # Some might be only date without time, or different format. Trying flexible parsing.
    df['DATA'] = pd.to_datetime(df['DAT_EMBARGO'], errors='coerce')
    df['ANO'] = df['DATA'].dt.year
    
    df_filtered = df[df['ANO'].isin(YEARS)]
    
    # QTD_AREA_EMBARGADA
    df_filtered['QTD_AREA_EMBARGADA'] = df_filtered['QTD_AREA_EMBARGADA'].astype(str).str.replace(',', '.').astype(float)
    
    print(f"Total registros filtrados (2022-2026): {len(df_filtered)}")
    
    summary = df_filtered.groupby('ANO').agg({
        'SEQ_TAD': 'count',
        'QTD_AREA_EMBARGADA': 'sum'
    }).rename(columns={'SEQ_TAD': 'Qtd Embargos', 'QTD_AREA_EMBARGADA': 'Área Embargada (ha)'})
    
    print(summary)
    
    print("\nTop 5 Estados por Ano (Qtd Embargos):")
    for year in YEARS:
        df_year = df_filtered[df_filtered['ANO'] == year]
        if not df_year.empty:
            print(f"\n{year}:")
            print(df_year['UF'].value_counts().head(5))

analyze_autos(csv_auto_path)
analyze_embargos(csv_embargo_path)
