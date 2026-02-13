import pandas as pd
import os
import urllib.parse

def generate_enrichment_csv():
    file_path = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\RELATORIO_MAPBIOMAS_API.csv"
    output_path = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\VITRINE_NULIDADE_ALTA.csv"
    
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return

    # Ler o relatório completo
    # Usando sep=';' e encoding='utf-8-sig' conforme definido no cliente API
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
    
    # Filtrar apenas Nulidade Alta (95%)
    # A coluna no CSV é 'CHANCE_NULIDADE' e contém valores como '95%', '60%', etc.
    df_vitrine = df[df['CHANCE_NULIDADE'].astype(str).str.contains('95')].copy()
    
    # Converter VALOR_MULTA para numérico (já está vindo como float no CSV atual)
    df_vitrine['VALOR_NUMERICO'] = pd.to_numeric(df_vitrine['VALOR_MULTA'], errors='coerce')
    
    # Ordenar do maior para o menor
    df_vitrine = df_vitrine.sort_values(by='VALOR_NUMERICO', ascending=False)
    
    # Formatar VALOR_MULTA para exibição amigável "R$ 50.000.000,00"
    def format_currency(val):
        try:
            return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(val)

    df_vitrine['VALOR_MULTA_PAGO'] = df_vitrine['VALOR_NUMERICO'].apply(format_currency)
    def make_google_link(row):
        query = f"{row['NOME_INFRATOR']} ambiental multa"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    def make_linkedin_link(row):
        query = f"site:linkedin.com/in/ {row['NOME_INFRATOR']}"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    def make_econodata_link(row):
        query = f"site:econodata.com.br {row['NOME_INFRATOR']}"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    def make_jusbrasil_link(row):
        query = f'"{row["NOME_INFRATOR"]}" processo ambiental'
        return f"https://www.jusbrasil.com.br/busca?q={urllib.parse.quote(query)}"

    df_vitrine['LINK_GOOGLE'] = df_vitrine.apply(make_google_link, axis=1)
    df_vitrine['LINK_LINKEDIN'] = df_vitrine.apply(make_linkedin_link, axis=1)
    df_vitrine['LINK_ECONODATA'] = df_vitrine.apply(make_econodata_link, axis=1)
    df_vitrine['LINK_JUSBRASIL'] = df_vitrine.apply(make_jusbrasil_link, axis=1)
    
    # Remover coluna auxiliar
    df_vitrine = df_vitrine.drop(columns=['VALOR_NUMERICO'])
    
    # Salvar a nova planilha
    df_vitrine.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"✅ Vitrine gerada com sucesso: {len(df_vitrine)} casos de alta nulidade encontrados.")
    print(f"📍 Local: {output_path}")

if __name__ == "__main__":
    generate_enrichment_csv()
