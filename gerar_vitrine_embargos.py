import pandas as pd
import os
import urllib.parse

def generate_enrichment_csv():
    file_path = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\RELATORIO_MAPBIOMAS_API.csv"
    output_path = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\VITRINE_EMBARGOS_ALTA.csv"
    
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return

    # Ler o relatório completo
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
    
    # Filtrar apenas Embargos (60% de chance de nulidade)
    df_vitrine = df[df['CHANCE_NULIDADE'].astype(str).str.contains('60')].copy()
    
    # Converter VALOR_MULTA para numérico para ordenação
    df_vitrine['VALOR_NUMERICO'] = pd.to_numeric(df_vitrine['VALOR_MULTA'], errors='coerce')
    
    # Ordenar do maior para o menor
    df_vitrine = df_vitrine.sort_values(by='VALOR_NUMERICO', ascending=False)
    
    # Formatar VALOR_MULTA para exibição amigável
    def format_currency(val):
        try:
            return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(val)

    df_vitrine['VALOR_MULTA_PAGO'] = df_vitrine['VALOR_NUMERICO'].apply(format_currency)

    # Links de enriquecimento
    def make_google_link(row):
        query = f"{row['NOME_INFRATOR']} ambiental multa"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    def make_linkedin_link(row):
        query = f"site:linkedin.com/in/ {row['NOME_INFRATOR']}"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    def make_econodata_link(row):
        query = f"site:econodata.com.br {row['NOME_INFRATOR']}"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    df_vitrine['LINK_GOOGLE'] = df_vitrine.apply(make_google_link, axis=1)
    df_vitrine['LINK_LINKEDIN'] = df_vitrine.apply(make_linkedin_link, axis=1)
    df_vitrine['LINK_ECONODATA'] = df_vitrine.apply(make_econodata_link, axis=1)
    
    # Remover coluna auxiliar
    df_vitrine = df_vitrine.drop(columns=['VALOR_NUMERICO'])
    
    # Salvar a nova planilha
    df_vitrine.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"✅ Vitrine de Embargos gerada com sucesso: {len(df_vitrine)} casos encontrados.")
    print(f"📍 Local: {output_path}")

if __name__ == "__main__":
    generate_enrichment_csv()
