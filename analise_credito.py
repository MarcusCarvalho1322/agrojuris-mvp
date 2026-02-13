import pandas as pd
import os
import gzip
from datetime import datetime

# Configuração
BASE_DIR = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\dados_bc"
FILES = [
    "SICOR_CONTRATOS_MUNICIPIO_2022.gz",
    "SICOR_CONTRATOS_MUNICIPIO_2023.gz",
    "SICOR_CONTRATOS_MUNICIPIO_2024.gz",
    "SICOR_CONTRATOS_MUNICIPIO_2025.gz"
]

def processar_dados():
    print(">>> Processando Dados de Crédito Rural (SICOR)...")
    
    cols = [
        'nomeUF', 'Municipio', 'codMunicIbge', 'MesEmissao', 'AnoEmissao',
        'VlCusteio', 'VlInvestimento', 'VlComercializacao', 'VlIndustrializacao'
    ]
    value_cols = ['VlCusteio', 'VlInvestimento', 'VlComercializacao', 'VlIndustrializacao']
    
    # Acumuladores
    total_por_ano = {}
    total_por_tipo = {c.replace('Vl', ''): 0.0 for c in value_cols}
    total_por_uf = {}
    total_por_mun = {} # (UF, MUN) -> VAL
    total_geral = 0.0
    total_por_mes = {}

    for filename in FILES:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            print(f"   Lendo e agregando {filename}...")
            try:
                # Ler em chunks se necessário, mas dataframe inteiro deve caber. 
                # Agregando por arquivo para economizar memória.
                # Low memory false e encoding latin-1
                df = pd.read_csv(filepath, compression='gzip', sep=';', encoding='latin-1', usecols=cols, decimal='.', low_memory=False)
                
                # Converter valores (garantir float)
                for col in value_cols:
                    # Remover possiveis pontos de milhar, trocar virgula por ponto se necessario
                    if df[col].dtype == 'object':
                         df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                df['VALOR_TOTAL'] = df[value_cols].sum(axis=1)
                
                # Agregar Ano
                ano_agg = df.groupby('AnoEmissao')['VALOR_TOTAL'].sum()
                for ano, val in ano_agg.items():
                    total_por_ano[ano] = total_por_ano.get(ano, 0) + val
                    
                # Agregar Tipo
                for col in value_cols:
                    tipo = col.replace('Vl', '')
                    total_por_tipo[tipo] += df[col].sum()
                    
                # Agregar UF
                uf_agg = df.groupby('nomeUF')['VALOR_TOTAL'].sum()
                for uf, val in uf_agg.items():
                    total_por_uf[uf] = total_por_uf.get(uf, 0) + val
                    
                # Agregar Municipio
                mun_agg = df.groupby(['nomeUF', 'Municipio'])['VALOR_TOTAL'].sum()
                for (uf, mun), val in mun_agg.items():
                    chave = (uf, mun)
                    total_por_mun[chave] = total_por_mun.get(chave, 0) + val
                    
                # Agregar Mes
                mes_agg = df.groupby('MesEmissao')['VALOR_TOTAL'].sum()
                for mes, val in mes_agg.items():
                    total_por_mes[mes] = total_por_mes.get(mes, 0) + val
                
                total_geral += df['VALOR_TOTAL'].sum()
                
                del df # Liberar memoria
                
            except Exception as e:
                print(f"   Erro ao processar {filename}: {e}")
        else:
            print(f"   Arquivo não encontrado: {filename}")

    return {
        'total_geral': total_geral,
        'total_por_ano': total_por_ano,
        'total_por_tipo': total_por_tipo,
        'total_por_uf': total_por_uf,
        'total_por_mun': total_por_mun,
        'total_por_mes': total_por_mes
    }

def gerar_relatorio(dados):
    print("\n>>> Gerando Relatório Final...")
    
    str_rel = "# RELATÓRIO DO MERCADO DE CRÉDITO RURAL (2022-2025)\n"
    str_rel += f"Fonte: Banco Central do Brasil (SICOR) - Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    str_rel += f"## VOLUME TOTAL CONCEDIDO: R$ {dados['total_geral']:,.2f}\n\n"
    
    # Por Ano
    str_rel += "### Evolução Anual (Crédito Concedido)\n"
    # Ordenar anos
    anos = sorted(dados['total_por_ano'].keys())
    for ano in anos:
        str_rel += f"- **{int(ano)}**: R$ {dados['total_por_ano'][ano]:,.2f}\n"
    str_rel += "\n"
    
    # Por Tipo
    str_rel += "### Finalidade do Crédito\n"
    tipos_sorted = sorted(dados['total_por_tipo'].items(), key=lambda x: x[1], reverse=True)
    for tipo, val in tipos_sorted:
        str_rel += f"- **{tipo}**: R$ {val:,.2f}\n"
    str_rel += "\n"
    
    # Top 10 Estados
    str_rel += "### Top 10 Estados (Volume Financeiro)\n"
    uf_sorted = sorted(dados['total_por_uf'].items(), key=lambda x: x[1], reverse=True)[:10]
    for uf, val in uf_sorted:
        str_rel += f"1. **{uf}**: R$ {val:,.2f}\n"
    str_rel += "\n"
    
    # Top 20 Municipios
    str_rel += "### Top 20 Municípios (Alvos Prioritários)\n"
    mun_sorted = sorted(dados['total_por_mun'].items(), key=lambda x: x[1], reverse=True)[:20]
    
    rank = 1
    for (uf, mun), val in mun_sorted:
        str_rel += f"{rank}. **{mun}/{uf}**: R$ {val:,.2f}\n"
        rank += 1
        
    output_path = os.path.join(r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie", "RELATORIO_CREDITO_RURAL_2022-2025.md")
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(str_rel)
        
    print(f"Relatório salvo em: {output_path}")
    print(str_rel)

if __name__ == "__main__":
    dados = processar_dados()
    if dados['total_geral'] > 0:
        gerar_relatorio(dados)
