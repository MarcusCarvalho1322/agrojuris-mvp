import pandas as pd
from datetime import datetime, timedelta
import os

# CONFIG
BASE_PATH = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie"
INPUT_FILE = "LISTA_FINAL_ATAQUE_COMERCIAL_2026_DIAMANTE_ENRIQUECIDA_OSINT.csv"
OUTPUT_FILE = "LISTA_FINAL_ATAQUE_COMERCIAL_2026_DIAMANTE_6MESES_OFF.csv"

# DATE CONFIG
CURRENT_DATE = datetime(2026, 1, 12) # User context date
CUTOFF_DATE = CURRENT_DATE - timedelta(days=180)

print(f"--- FILTRO DE OPPORTUNIDADE QUENTE (6 MESES OFF) ---")
print(f"Data Base: {CURRENT_DATE.date()}")
print(f"Data Corte: {CUTOFF_DATE.date()} (Multas posteriores a esta data)")

full_path_in = os.path.join(BASE_PATH, INPUT_FILE)
full_path_out = os.path.join(BASE_PATH, OUTPUT_FILE)

try:
    # Load Data
    print(f"Lendo: {INPUT_FILE}...")
    df = pd.read_csv(full_path_in, sep=';', encoding='utf-8-sig')
    
    # Convert Date
    # Looking for format YYYY-MM-DD
    df['DATA_OBJ'] = pd.to_datetime(df['DAT_HORA_AUTO_INFRACAO'], errors='coerce')
    
    # Filter
    df_hot = df[df['DATA_OBJ'] >= CUTOFF_DATE].copy()
    
    # Sort closest to expiration/action (Most recent first)
    df_hot = df_hot.sort_values(by='DATA_OBJ', ascending=False)
    
    # Clean up aux column
    df_hot = df_hot.drop(columns=['DATA_OBJ'])
    
    # Save
    df_hot.to_csv(full_path_out, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\n[SUCESSO] Lista HOT Gerada: {OUTPUT_FILE}")
    print(f"Leads Encontrados (Últimos 6 meses): {len(df_hot)}")
    print(f"Estes são os leads onde o prazo de defesa provavelmente ainda está aberto ou o 'calor' do momento é máximo.")

except Exception as e:
    print(f"[ERRO] {e}")
