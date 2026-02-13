import pandas as pd
import os
import glob
from datetime import datetime

# Configuração de caminhos
BASE_DIR = r"C:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\dados_ibama"
AUTO_INFRACAO_DIR = os.path.join(BASE_DIR, "auto_infracao")
TERMO_EMBARGO_FILE = os.path.join(BASE_DIR, "termo_embargo", "termo_embargo.csv")

# Anos de interesse
ANOS = [2022, 2023, 2024, 2025, 2026]

def carregar_autos_infracao():
    print(">>> Carregando Autos de Infração...")
    dfs = []
    
    # Colunas de interesse para otimizar memória
    cols = [
        'SEQ_AUTO_INFRACAO', 'NUM_AUTO_INFRACAO', 'VAL_AUTO_INFRACAO', 
        'DAT_HORA_AUTO_INFRACAO', 'UF', 'MUNICIPIO', 'DES_INFRACAO', 
        'TIPO_INFRACAO', 'NOME_INFRATOR', 'CPF_CNPJ_INFRATOR',
        'DS_BIOMAS_ATINGIDOS', 'SIT_CANCELADO'
    ]
    
    for ano in ANOS:
        filename = f"auto_infracao_ano_{ano}.csv"
        filepath = os.path.join(AUTO_INFRACAO_DIR, filename)
        
        if os.path.exists(filepath):
            print(f"   Lendo {filename}...")
            try:
                # O delimitador parece ser ponto e vírgula com base no head
                df = pd.read_csv(filepath, sep=';', usecols=cols, encoding='utf-8', on_bad_lines='skip', low_memory=False)
                df['ANO_FONTE'] = ano
                dfs.append(df)
            except Exception as e:
                print(f"   Erro ao ler {filename}: {e}")
        else:
            print(f"   Arquivo não encontrado: {filename}")
            
    if not dfs:
        return pd.DataFrame()
        
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Limpeza básica
    # Converter data
    full_df['DAT_HORA_AUTO_INFRACAO'] = pd.to_datetime(full_df['DAT_HORA_AUTO_INFRACAO'], errors='coerce')
    
    # Converter valor (pode estar com vírgula decimal)
    # Ex: 1500,00 -> 1500.00
    if full_df['VAL_AUTO_INFRACAO'].dtype == 'object':
        full_df['VAL_AUTO_INFRACAO'] = full_df['VAL_AUTO_INFRACAO'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        full_df['VAL_AUTO_INFRACAO'] = pd.to_numeric(full_df['VAL_AUTO_INFRACAO'], errors='coerce')
        
    return full_df

def carregar_embargos():
    print("\n>>> Carregando Termos de Embargo...")
    if not os.path.exists(TERMO_EMBARGO_FILE):
        print("   Arquivo termo_embargo.csv não encontrado.")
        return pd.DataFrame()
        
    # Colunas prováveis (preciso inferir ou usar todas e filtrar depois, vou usar chunks se for muito grande, mas 160MB é ok pra memória moderna)
    # Vou ler apenas colunas essenciais se souber os nomes, mas não vi o header desse arquivo.
    # Vou ler as primeiras linhas para pegar colunas
    try:
        header = pd.read_csv(TERMO_EMBARGO_FILE, sep=';', nrows=0, encoding='utf-8').columns.tolist()
        print(f"   Colunas detectadas: {header}")
        
        # Filtros de data geralmente são DAT_EMBARGO ou similar
        # Vou tentar ler com parse de datas se existirem colunas com 'DAT'
        date_cols = [c for c in header if 'DAT' in c]
        
        df = pd.read_csv(TERMO_EMBARGO_FILE, sep=';', encoding='utf-8', on_bad_lines='skip', low_memory=False)
        
        # Tentar converter colunas de data
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
        # Filtrar por data (2022+)
        # Assumindo que DAT_TAD seja a data do termo (TAD = Termo de Apreensão/Depósito? Não, Embargo é TE? Vamos procurar colunas de data)
        # Geralmente DAT_EMBARGO
        
        col_data = None
        if 'DAT_EMBARGO' in df.columns:
            col_data = 'DAT_EMBARGO'
        elif 'DAT_TAD' in df.columns:
            col_data = 'DAT_TAD'
        elif 'DAT_HORA_AUTO_INFRACAO' in df.columns: # As vezes é vinculado
             col_data = 'DAT_HORA_AUTO_INFRACAO'
             
        if col_data:
            print(f"   Filtrando por data usando coluna: {col_data}")
            df = df[df[col_data] >= '2022-01-01']
        else:
            print("   Não foi possível identificar coluna de data para filtro. Analisando tudo.")
            
        return df
    except Exception as e:
        print(f"   Erro ao ler embargos: {e}")
        return pd.DataFrame()

def gerar_relatorio(df_autos, df_embargos):
    print("\n>>> Gerando Relatório Consolidado...")
    
    str_relatorio = "# RELATÓRIO CONSOLIDADO DE FISCALIZAÇÃO IBAMA (2022-2026)\n"
    str_relatorio += f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    # --- AUTOS DE INFRAÇÃO ---
    str_relatorio += "## 1. ANÁLISE DE AUTOS DE INFRAÇÃO\n\n"
    
    if not df_autos.empty:
        # Total geral
        total_autos = len(df_autos)
        total_valor = df_autos['VAL_AUTO_INFRACAO'].sum()
        
        str_relatorio += f"- **Total de Autuações:** {total_autos}\n"
        str_relatorio += f"- **Valor Total de Multas:** R$ {total_valor:,.2f}\n\n"
        
        # Por Ano
        str_relatorio += "### Distribuição por Ano\n"
        por_ano = df_autos.groupby(df_autos['DAT_HORA_AUTO_INFRACAO'].dt.year).size()
        valor_por_ano = df_autos.groupby(df_autos['DAT_HORA_AUTO_INFRACAO'].dt.year)['VAL_AUTO_INFRACAO'].sum()
        
        for ano in por_ano.index:
            str_relatorio += f"- **{int(ano)}**: {por_ano[ano]} autuações (R$ {valor_por_ano[ano]:,.2f})\n"
        str_relatorio += "\n"
        
        # Top 5 Estados
        str_relatorio += "### Top 5 Estados com Mais Autuações\n"
        top_uf = df_autos['UF'].value_counts().head(5)
        for uf, count in top_uf.items():
            str_relatorio += f"- **{uf}**: {count}\n"
        str_relatorio += "\n"
        
        # Top 5 Infrações (Tipo)
        str_relatorio += "### Top 5 Tipos de Infração\n"
        if 'TIPO_INFRACAO' in df_autos.columns:
            top_tipo = df_autos['TIPO_INFRACAO'].value_counts().head(5)
            for tipo, count in top_tipo.items():
                str_relatorio += f"- **{tipo}**: {count}\n"
        str_relatorio += "\n"
        
        # Biomas
        str_relatorio += "### Biomas Afetados\n"
        if 'DS_BIOMAS_ATINGIDOS' in df_autos.columns:
            top_bioma = df_autos['DS_BIOMAS_ATINGIDOS'].value_counts().head(5)
            for bioma, count in top_bioma.items():
                str_relatorio += f"- **{bioma}**: {count}\n"
        str_relatorio += "\n"
        
    else:
        str_relatorio += "Nenhum dado de auto de infração encontrado.\n\n"

    # --- EMBARGOS ---
    str_relatorio += "## 2. ANÁLISE DE EMBARGOS\n\n"
    
    if not df_embargos.empty:
        str_relatorio += f"- **Total de Áreas Embargadas (registros):** {len(df_embargos)}\n"
        
        # Tentar somar área se existir coluna
        col_area = None
        for c in df_embargos.columns:
            if 'AREA' in c and 'TAT' in c: # QTD_AREA_EMBARGADA?
                col_area = c
                break
        
        if col_area:
             # Limpeza area
            if df_embargos[col_area].dtype == 'object':
                df_embargos[col_area] = df_embargos[col_area].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_embargos[col_area] = pd.to_numeric(df_embargos[col_area], errors='coerce')
                
            total_area = df_embargos[col_area].sum()
            str_relatorio += f"- **Área Total Embargada Estimada:** {total_area:,.2f} ha\n"
            
        # Top 5 Municípios Embargo
        str_relatorio += "\n### Top 5 Municípios com Embargos\n"
        if 'NO_MUNICIPIO' in df_embargos.columns:
            top_mun = df_embargos['NO_MUNICIPIO'].value_counts().head(5)
            for mun, count in top_mun.items():
                str_relatorio += f"- **{mun}**: {count}\n"
        elif 'MUNICIPIO' in df_embargos.columns:
            top_mun = df_embargos['MUNICIPIO'].value_counts().head(5)
            for mun, count in top_mun.items():
                str_relatorio += f"- **{mun}**: {count}\n"
                
    else:
        str_relatorio += "Nenhum dado de embargo encontrado para o período ou erro na leitura.\n"

    # Salvar
    output_file = os.path.join(r"C:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie", "RELATORIO_CONSOLIDADO_IBAMA_2022-2026.md")
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(str_relatorio)
        
    print(f"\nRelatório salvo em: {output_file}")
    print(str_relatorio)

if __name__ == "__main__":
    df_autos = carregar_autos_infracao()
    df_embargos = carregar_embargos()
    gerar_relatorio(df_autos, df_embargos)
