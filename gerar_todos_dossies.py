import pandas as pd
import os

def generate_all_dossiers():
    csv_path = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\VITRINE_NULIDADE_ALTA.csv"
    output_dir = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\DOSSIES_NULIDADE_ALTA"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(csv_path):
        print("Erro: CSV de nulidade não encontrado.")
        return

    df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
    
    template = """# DOSSIÊ DE NULIDADE AMBIENTAL - ESTRATÉGICO 2026
**ALVO: {nome}**
**VALOR DA CAUSA: {valor_formatado}**

---

## 1. IDENTIFICAÇÃO DO PROCESSO
- **INFRATOR:** {nome}
- **VALOR NOMINAL DA MULTA:** {valor_formatado}
- **LOCALIZAÇÃO:** 
  - **LATITUD:** {lat}
  - **LONGITUDE:** {lon}
  - [Ver no Google Maps](https://www.google.com/maps/search/?api=1&query={lat},{lon})

## 2. ANÁLISE TÉCNICA (IA AGRODEFESA)
- **STATUS:** ✅ NULIDADE ALTA (95% de probabilidade)
- **FUNDAMENTAÇÃO JURÍDICA:** {motivo}
- **DADOS DA AUTORIZAÇÃO:** 
  - **Área Autorizada:** {area_aut} ha
  - **Área do Alerta:** {area_ha} ha
- **STATUS IA:** {status_ia}

## 3. PROVAS TÉCNICAS (MAPBIOMAS)
- **CÓDIGO DO ALERTA:** {alerta_code}
- **EVIDÊNCIA:** Cruzamento geoespacial positiva para autorização vigente.

## 4. INVESTIGAÇÃO DE PERFIL (ENRIQUECIMENTO)
- **BUSCA POR PRECEDENTES:** [Pesquisar Histórico Ambiental]({link_google})
- **PERFIL PROFISSIONAL:** [Localizar Decisor no LinkedIn]({link_linkedin})
- **PORTE ECONÔMICO:** [Empresas Vinculadas - Econodata]({link_econodata})
- **PROCESSOS JUDICIAIS:** [Verificar Advogado no Jusbrasil]({link_jusbrasil})

---

## 5. RECOMENDAÇÃO NEGOCIAL
Apresentar este relatório enfatizando a nulidade técnica. Economia estimada de {valor_formatado}.

---
*Gerado automaticamente pelo Sistema AgroDefesa Intelligence - 14/01/2026*
"""

    count = 0
    for _, row in df.iterrows():
        # Limpar nome para o arquivo
        safe_name = "".join([c for c in str(row['NOME_INFRATOR']) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
        filename = f"{count+1:03d}_{safe_name}.md"
        file_full_path = os.path.join(output_dir, filename)
        
        dossie_content = template.format(
            nome=row['NOME_INFRATOR'],
            valor_formatado=row['VALOR_MULTA_PAGO'],
            lat=row['LAT'],
            lon=row['LON'],
            motivo=row['MOTIVO_IA'],
            area_aut=row['AUTORIZACAO_AREA'],
            area_ha=row['AREA_HA'],
            status_ia=row['STATUS_IA'],
            alerta_code=row['ALERTA_CODE'],
            link_google=row['LINK_GOOGLE'],
            link_linkedin=row['LINK_LINKEDIN'],
            link_econodata=row['LINK_ECONODATA'],
            link_jusbrasil=row.get('LINK_JUSBRASIL', '#')
        )
        
        with open(file_full_path, "w", encoding="utf-8-sig") as f:
            f.write(dossie_content)
        count += 1

    print(f"✅ Sucesso: {count} dossiês gerados na pasta {output_dir}")

if __name__ == "__main__":
    generate_all_dossiers()
