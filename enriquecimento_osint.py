import pandas as pd
import urllib.parse
import os

# CONFIG
BASE_PATH = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie"
FILES_TO_PROCESS = [
    "LISTA_FINAL_ATAQUE_COMERCIAL_2026_DIAMANTE.csv",
    "LISTA_FINAL_ATAQUE_COMERCIAL_2026_OURO.csv"
]

def clean_cpf_cnpj(val):
    return ''.join(filter(str.isdigit, str(val)))

def generate_osint_links(row):
    nome = str(row['NOME_INFRATOR']).strip()
    doc = clean_cpf_cnpj(row['CPF_CNPJ_INFRATOR'])
    municipio = str(row['MUNICIPIO']).strip()
    uf = str(row['UF']).strip()
    local = str(row['DES_LOCAL_INFRACAO']).strip()
    
    links = {}
    
    # URL Encoding safe parameters
    q_nome = urllib.parse.quote(nome)
    q_municipio = urllib.parse.quote(municipio)
    q_local = urllib.parse.quote(local)
    
    # LOGIC: PJ vs PF
    if len(doc) > 11:
        # PESSOA JURIDICA (CNPJ) -> Buscar Dados Cadastrais (Telefone Obrigatório)
        links['LINK_RAPIDO_CONTATO'] = f"https://cnpj.biz/{doc}"
        links['LINK_GOOGLE_MAPS'] = f"https://www.google.com/maps/search/{q_nome}+{q_municipio}+{uf}"
        links['LINK_SOCIO_PROPRIETARIO'] = f"https://www.google.com/search?q=sócio+{q_nome}+telefone"
    else:
        # PESSOA FISICA (CPF) -> Buscar Fazenda e Vínculos
        # Search 1: Nome + Cidade + Telefone
        links['LINK_RAPIDO_CONTATO'] = f"https://www.google.com/search?q={q_nome}+{q_municipio}+telefone+contato"
        
        # Search 2: Fazenda Especifica (O mais valioso)
        if len(local) > 3 and "nan" not in local.lower():
            links['LINK_GOOGLE_MAPS'] = f"https://www.google.com/search?q={q_local}+{q_municipio}+proprietário"
        else:
            links['LINK_GOOGLE_MAPS'] = ""
            
        # Search 3: Jusbrasil (Advogado)
        links['LINK_SOCIO_PROPRIETARIO'] = f"https://www.jusbrasil.com.br/busca?q={q_nome}+{municipio}"
        
    return pd.Series(links)

def process_file(filename):
    full_path = os.path.join(BASE_PATH, filename)
    if not os.path.exists(full_path):
        print(f"Arquivo não encontrado: {full_path}")
        return

    print(f">>> Processando Enriquecimento OSINT: {filename}...")
    
    try:
        df = pd.read_csv(full_path,sep=';', encoding='utf-8-sig')
        
        # Apply Logic
        osint_cols = df.apply(generate_osint_links, axis=1)
        
        # Concatenate results
        df_final = pd.concat([df, osint_cols], axis=1)
        
        # Reorder to put links near the beginning for easier viewing in cell phones/excel
        cols = list(df_final.columns)
        # Move links to position 2 (after name)
        new_order = ['NOME_INFRATOR', 'LINK_RAPIDO_CONTATO', 'VALOR_MULTA', 'MUNICIPIO', 'LINK_GOOGLE_MAPS', 'LINK_SOCIO_PROPRIETARIO'] + [c for c in cols if c not in ['NOME_INFRATOR', 'LINK_RAPIDO_CONTATO', 'VALOR_MULTA', 'MUNICIPIO', 'LINK_GOOGLE_MAPS', 'LINK_SOCIO_PROPRIETARIO']]
        df_final = df_final[new_order]
        
        # Save
        new_filename = filename.replace(".csv", "_ENRIQUECIDA_OSINT.csv")
        new_path = os.path.join(BASE_PATH, new_filename)
        df_final.to_csv(new_path, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"   [SUCESSO] Gerado: {new_filename}")
        print(f"   Links gerados para {len(df_final)} leads.")
        
    except Exception as e:
        print(f"   [ERRO] Falha ao processar {filename}: {e}")

# EXECUTION
if __name__ == "__main__":
    print("--- INICIANDO ROBÔ DE ENRIQUECIMENTO OSINT ---")
    for f in FILES_TO_PROCESS:
        process_file(f)
