"""
MapBiomas Alerta - Cliente API Oficial (GraphQL V2)
====================================================
Solução 100% via API - sem scraping, sem erros de navegador.

Fluxo:
1. SignIn para obter Bearer Token
2. Query `pointInformation` para buscar alertas por coordenadas (bounding box)
3. Query `alert` para detalhes completos do alerta (incluindo autorizações)
4. Exporta relatório estruturado para análise jurídica
"""

import os
import requests
import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# ==========================
# CONFIGURAÇÃO
# ==========================
API_ENDPOINT = "https://plataforma.alerta.mapbiomas.org/api/v2/graphql"
INPUT_CSV = Path(__file__).parent / "LISTA_DIAMANTE_MATRIZ_TESES_2026.csv"
OUTPUT_REPORT = Path(__file__).parent / "RELATORIO_MAPBIOMAS_API.csv"
LOG_FILE = Path(__file__).parent / "log_api_mapbiomas.txt"
DASHBOARD_FILE = Path(__file__).parent / "DASHBOARD_RESULTADOS.txt"

# Credenciais - use variaveis de ambiente
EMAIL = os.getenv("MAPBIOMAS_EMAIL")
PASSWORD = os.getenv("MAPBIOMAS_PASSWORD")


def log(msg: str):
    """Log para arquivo e console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def graphql_request(query: str, variables: dict = None, token: str = None, retries: int = 3) -> dict:
    """Executa uma requisição GraphQL com retry em caso de falha de rede."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    for i in range(retries):
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if i < retries - 1:
                log(f"  [RETRY {i+1}/{retries}] Erro de conexão: {e}. Aguardando 30s...")
                time.sleep(30)
            else:
                raise e


def sign_in(email: str, password: str) -> str:
    """Autentica e retorna o Bearer Token."""
    query = """
    mutation signIn($email: String!, $password: String!) {
      signIn(email: $email, password: $password) {
        token
      }
    }
    """
    variables = {"email": email, "password": password}
    result = graphql_request(query, variables)
    
    if "errors" in result:
        raise Exception(f"Erro de autenticação: {result['errors']}")
    
    return result["data"]["signIn"]["token"]


def get_alerts_by_bounding_box(token: str, lat: float, lon: float, radius: float = 0.1) -> List[dict]:
    """
    Busca alertas dentro de um bounding box ao redor de uma coordenada.
    Usa a query 'alerts' que é mais robusta que 'pointInformation'.
    O radius define o tamanho da caixa de busca em graus (~10km por 0.1).
    """
    query = """
    query alerts($boundingBox: [Float!], $startDate: BaseDate, $limit: Int) {
      alerts(
        boundingBox: $boundingBox,
        startDate: $startDate,
        limit: $limit,
        statusName: "published"
      ) {
        collection {
          alertCode
          areaHa
          detectedAt
          publishedAt
          statusName
          crossedDeforestationAuthorizationsArea
          crossedEmbargoesRuralPropertiesTotal
          ruralPropertiesTotal
          sources
          crossedStates
          crossedCities
        }
        metadata {
          totalCount
        }
      }
    }
    """
    # boundingBox no formato [swLng, swLat, neLng, neLat]
    variables = {
        "boundingBox": [lon - radius, lat - radius, lon + radius, lat + radius],
        "startDate": "2019-01-01",
        "limit": 10
    }
    
    try:
        result = graphql_request(query, variables, token)
        
        if "errors" in result:
            log(f"  Aviso API: {result['errors'][0].get('message', 'Erro desconhecido')}")
            return []
        
        collection = result.get("data", {}).get("alerts", {}).get("collection", [])
        return collection
    except Exception as e:
        log(f"  Erro na requisição: {str(e)[:100]}")
        return []


def get_alert_details(token: str, alert_code: int) -> dict:
    """Busca detalhes completos de um alerta específico."""
    query = """
    query alert($alertCode: Int!) {
      alert(alertCode: $alertCode) {
        alertCode
        areaHa
        detectedAt
        publishedAt
        statusName
        coordenates {
          latitude
          longitude
        }
        crossedBiomes
        crossedCities
        crossedStates
        crossedDeforestationAuthorizationsActivities
        crossedDeforestationAuthorizationsArea
        crossedDeforestationAuthorizationsCategories
        crossedDeforestationAuthorizationsList
        crossedEmbargoesRuralPropertiesTotal
        crossedConservationUnits
        crossedIndigenousLands
        crossedSettlements
        ruralPropertiesTotal
        ruralPropertiesCodes
        sources
        warnings {
          pt
        }
        supportCaseAuthorizations {
          authorizedAreaHa
          authorizingAgency
          documentIssueDate
          expirationDate
          processNumber
          supportCaseType
        }
      }
    }
    """
    variables = {"alertCode": alert_code}
    
    result = graphql_request(query, variables, token)
    
    if "errors" in result:
        log(f"Erro ao buscar alerta {alert_code}: {result['errors']}")
        return {}
    
    return result.get("data", {}).get("alert", {})


def analyze_alert_for_nullity(alert: dict) -> Dict[str, str]:
    """
    Analisa um alerta e determina chances de nulidade baseado em:
    - Autorizações de desmatamento (ASV)
    - Sobreposição com áreas autorizadas
    - Embargos existentes
    """
    auth_area = alert.get("crossedDeforestationAuthorizationsArea", 0) or 0
    auth_activities = alert.get("crossedDeforestationAuthorizationsActivities", []) or []
    auth_categories = alert.get("crossedDeforestationAuthorizationsCategories", []) or []
    support_cases = alert.get("supportCaseAuthorizations", []) or []
    embargoes = alert.get("crossedEmbargoesRuralPropertiesTotal", 0) or 0
    warnings = alert.get("warnings", {})
    
    # Lógica de classificação
    if auth_area > 0 or len(support_cases) > 0:
        status = "NULIDADE ALTA"
        chance = "95%"
        motivo = f"Autorização detectada: {auth_area:.2f} ha. Atividades: {', '.join(auth_activities) if auth_activities else 'N/A'}. Categorias: {', '.join(auth_categories) if auth_categories else 'N/A'}"
    elif embargoes > 0:
        status = "VERIFICAR EMBARGO"
        chance = "60%"
        motivo = f"Propriedade já embargada ({embargoes} embargos). Possível bis in idem."
    elif warnings:
        status = "REVISAR"
        chance = "40%"
        motivo = f"Aviso do sistema: {warnings.get('pt', 'N/A')}"
    else:
        status = "ANALISAR MANUAL"
        chance = "20%"
        motivo = "Sem evidências automáticas de autorização no sistema."
    
    return {"status": status, "chance": chance, "motivo": motivo}


def read_leads() -> List[Dict[str, str]]:
    """Lê os leads da Lista Diamante."""
    leads = []
    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if "NULIDADE" in row.get("TESE_PRIMARIA", ""):
                leads.append(row)
    return leads


def update_dashboard(total_total: int):
    """Atualiza o arquivo DASHBOARD_RESULTADOS.txt com resumo simplificado."""
    try:
        results = []
        if OUTPUT_REPORT.exists():
            with open(OUTPUT_REPORT, "r", newline="", encoding="utf-8-sig") as f:
                results = list(csv.DictReader(f, delimiter=";"))
        
        wins = [r for r in results if r["STATUS_IA"] == "NULIDADE ALTA"]
        embargos = [r for r in results if r["STATUS_IA"] == "VERIFICAR EMBARGO"]
        
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE MONITORAMENTO - AGRODEFESA / MAPBIOMAS\n")
            f.write("==================================================\n")
            f.write(f"Última Atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            f.write(f"Progresso Geral: {len(results)} / {total_total} ({(len(results)/total_total*100):.1f}%)\n")
            f.write(f"Vitrinas (Nulidade Alta): {len(wins)}\n")
            f.write(f"Casos de Embargo/Bis in Idem: {len(embargos)}\n\n")
            
            f.write("LISTA DE GRANDES OPORTUNIDADES (NULIDADE ALTA):\n")
            f.write("-" * 50 + "\n")
            if not wins:
                f.write("Ainda processando... nenhum caso de 95% encontrado ainda.\n")
            for w in wins:
                f.write(f"- {w['NOME_INFRATOR']}: R$ {float(w['VALOR_MULTA']):,.2f} | Alerta: {w['ALERTA_CODE']}\n")
            
            f.write("\n\n(Dica: Abra o arquivo RELATORIO_MAPBIOMAS_API.csv no Excel para ver tudo)\n")
    except Exception as e:
        log(f"Erro ao atualizar dashboard: {e}")


def save_report(results: List[dict], total_leads: int):
    """Salva os resultados agregando aos existentes com retry para casos de arquivo aberto."""
    if not results:
        update_dashboard(total_leads)
        return
        
    for attempt in range(5):
        try:
            # Carregar resultados anteriores se existirem
            existing_results = []
            if OUTPUT_REPORT.exists():
                with open(OUTPUT_REPORT, "r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    existing_results = list(reader)

            # Agregar novos resultados
            all_results = existing_results + results

            # Remover duplicatas (manter o processado recentemente)
            seen = set()
            final_results = []
            for r in reversed(all_results):
                nome = r.get("NOME_INFRATOR")
                if nome not in seen:
                    seen.add(nome)
                    final_results.append(r)
            final_results.reverse()
            
            # Salvar
            if final_results:
                keys = final_results[0].keys()
                with open(OUTPUT_REPORT, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=keys, delimiter=";")
                    writer.writeheader()
                    writer.writerows(final_results)
            
            update_dashboard(total_leads)
            return # Sucesso
        except PermissionError:
            log(f"  [AVISO] Arquivo Excel aberto. Feche-o para salvar! Tentativa {attempt+1}/5 em 30s...")
            time.sleep(30)
        except Exception as e:
            log(f"Erro ao salvar relatório: {e}")
            break


def process_leads(token: str, leads: List[dict], limit: int = None, skip_processed: bool = True):
    """Processa os leads e gera o relatório, revisando o que estiver errado."""
    results = []
    processed_count = 0

    # Verificar o que já foi feito com qualidade
    already_done = set()
    leads_to_recheck = set()
    
    if skip_processed and OUTPUT_REPORT.exists():
        try:
            with open(OUTPUT_REPORT, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    status = row.get("STATUS_IA", "")
                    nome = row.get("NOME_INFRATOR")
                    # Se tiver status positivo ou "SEM ALERTAS" definitivo, pulamos
                    if status in ["NULIDADE ALTA", "VERIFICAR EMBARGO", "REVISAR"]:
                        already_done.add(nome)
                    elif status == "ERRO" or status == "" or row.get("CHANCE_NULIDADE") == "0%":
                        # Marcar para revisão obrigatória se tiver erro ou chance 0 sem explicação
                        leads_to_recheck.add(nome)
            
            log(f"Qualidade: {len(already_done)} leads validados encontrados. Recheck de {len(leads_to_recheck)} falhas anteriores.")
        except Exception as e:
            log(f"Erro ao analisar qualidade do CSV: {e}")

    if limit:
        leads = leads[:limit]

    total = len(leads)
    log(f"Iniciando processamento/revisão de {total} leads via API...")
    
    # Inicializar dashboard
    save_report([], total)
    
    for i, lead in enumerate(leads, 1):
        nome = lead.get("NOME_INFRATOR") or lead.get("ï»¿NOME_INFRATOR") or "Desconhecido"
        
        # Pular apenas se for um sucesso de qualidade e estiver no CSV
        if skip_processed and nome in already_done and nome not in leads_to_recheck:
            continue
            
        valor = lead.get("VALOR_MULTA", "0")
        lat = lead.get("NUM_LATITUDE_AUTO", "0")
        lon = lead.get("NUM_LONGITUDE_AUTO", "0")
        
        try:
            lat = float(lat.replace(",", ".")) if lat else 0
            lon = float(lon.replace(",", ".")) if lon else 0
        except:
            lat, lon = 0, 0
        
        if lat == 0 or lon == 0:
            log(f"[{i}/{total}] {nome}: Coordenadas inválidas. Pulando.")
            continue
            
        # Validar se a coordenada está aproximadamente no Brasil
        # Lat: +5 a -34 | Lon: -34 a -74
        if not (-35 < lat < 6 and -75 < lon < -33):
            log(f"[{i}/{total}] {nome}: Coordenada fora do Brasil ({lat}, {lon}). Pulando.")
            results.append({
                "NOME_INFRATOR": nome,
                "VALOR_MULTA": valor,
                "LAT": lat,
                "LON": lon,
                "ALERTAS_ENCONTRADOS": 0,
                "STATUS_IA": "COORD_INVALIDA",
                "CHANCE_NULIDADE": "0%",
                "MOTIVO_IA": f"Coordenada ({lat}, {lon}) fora dos limites do Brasil.",
                "ALERTA_CODE": "",
                "AREA_HA": "",
                "AUTORIZACAO_AREA": ""
            })
            continue
        
        log(f"[{i}/{total}] Processando: {nome} (Lat: {lat}, Lon: {lon})")
        
        # 1. Buscar alertas na região (com retry)
        alerts = []
        for tentativa in range(3):
            try:
                alerts = get_alerts_by_bounding_box(token, lat, lon)
                break
            except Exception as e:
                log(f"  [RETRY {tentativa+1}/3] Erro busca alertas: {e}")
                time.sleep(2)
        
        if not alerts:
            log(f"  -> Nenhum alerta encontrado na região.")
            results.append({
                "NOME_INFRATOR": nome,
                "VALOR_MULTA": valor,
                "LAT": lat,
                "LON": lon,
                "ALERTAS_ENCONTRADOS": 0,
                "STATUS_IA": "SEM ALERTAS",
                "CHANCE_NULIDADE": "N/A",
                "MOTIVO_IA": "Nenhum alerta do MapBiomas na região da coordenada.",
                "ALERTA_CODE": "",
                "AREA_HA": "",
                "AUTORIZACAO_AREA": ""
            })
            continue
        
        # 2. Pegar o maior alerta (mais relevante)
        maior_alerta = max(alerts, key=lambda x: x.get("areaHa", 0))
        alert_code = maior_alerta.get("alertCode")
        
        # 3. Buscar detalhes completos (com retry)
        detalhes = {}
        for tentativa in range(3):
            try:
                detalhes = get_alert_details(token, alert_code) if alert_code else {}
                break
            except Exception as e:
                log(f"  [RETRY {tentativa+1}/3] Erro: {e}")
                time.sleep(2)
        
        # 4. Analisar para nulidade
        analise = analyze_alert_for_nullity(detalhes) if detalhes else {
            "status": "ERRO",
            "chance": "0%",
            "motivo": "Não foi possível obter detalhes do alerta."
        }
        
        results.append({
            "NOME_INFRATOR": nome,
            "VALOR_MULTA": valor,
            "LAT": lat,
            "LON": lon,
            "ALERTAS_ENCONTRADOS": len(alerts),
            "STATUS_IA": analise["status"],
            "CHANCE_NULIDADE": analise["chance"],
            "MOTIVO_IA": analise["motivo"],
            "ALERTA_CODE": alert_code or "",
            "AREA_HA": detalhes.get("areaHa", ""),
            "AUTORIZACAO_AREA": detalhes.get("crossedDeforestationAuthorizationsArea", 0)
        })
        
        log(f"  -> {analise['status']} ({analise['chance']})")
        processed_count += 1
        
        # Salvar periodicamente a cada 5 leads para não perder progresso
        if processed_count % 5 == 0:
            save_report(results, total)
            results = [] # Limpa a lista local após salvar para não duplicar no próximo save
            log(f"  [AUTO-SAVE] Progresso salvo no relatório.")

        # Pausa otimizada: 5 segundos (redução de 50%) para acelerar a captação
        time.sleep(5)

    # Salvar resultados finais
    if results:
        save_report(results, total)
def investigate_final_quality():
    """Analisa a qualidade final do documento gerado."""
    log("\n[4/4] INVESTIGAÇÃO DE QUALIDADE FINAL...")
    try:
        if not OUTPUT_REPORT.exists():
            log("❌ Arquivo de relatório não encontrado para auditoria.")
            return

        with open(OUTPUT_REPORT, "r", newline="", encoding="utf-8-sig") as f:
            data = list(csv.DictReader(f, delimiter=";"))

        total = len(data)
        duplicates = total - len(set(r["NOME_INFRATOR"] for r in data))
        nulidades = [r for r in data if r["STATUS_IA"] == "NULIDADE ALTA"]
        embargos = [r for r in data if r["STATUS_IA"] == "VERIFICAR EMBARGO"]
        nao_encontrados = [r for r in data if r["STATUS_IA"] == "SEM ALERTAS"]
        erros = [r for r in data if r["STATUS_IA"] == "ERRO"]

        quality_report = Path(__file__).parent / "AUDITORIA_QUALIDADE.txt"
        with open(quality_report, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE AUDITORIA DE QUALIDADE - MAPBIOMAS\n")
            f.write("==============================================\n")
            f.write(f"Data da Auditoria: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write(f"Total de Leads Analisados: {total}\n")
            f.write(f"Duplicidade Detectada: {duplicates} casos (removidos durante o processo)\n")
            f.write(f"Leads sem Alertas no MapBiomas: {len(nao_encontrados)} ({(len(nao_encontrados)/total*100):.1f}%)\n")
            f.write(f"Erros Técnicos Restantes: {len(erros)}\n\n")

            f.write("RESUMO DE TESES JURÍDICAS:\n")
            f.write(f"- Nulidade Alta (95%): {len(nulidades)} casos\n")
            f.write(f"- Bis in Idem / Embargo (60%): {len(embargos)} casos\n\n")

            f.write("TOP 10 CASOS POR VALOR DA MULTA (NULIDADES/EMBARGOS):\n")
            all_relevant = nulidades + embargos
            all_relevant.sort(key=lambda x: float(x["VALOR_MULTA"] or 0), reverse=True)
            for i, r in enumerate(all_relevant[:10], 1):
                f.write(f"{i}. {r['NOME_INFRATOR']} - R$ {float(r['VALOR_MULTA']):,.2f} ({r['STATUS_IA']})\n")

        log(f"✅ Auditoria concluída! Veja o arquivo: {quality_report}")
    except Exception as e:
        log(f"Erro na investigação de qualidade: {e}")


def main():
    """Função principal com auto-recuperação."""
    while True:
        try:
            log("=" * 60)
            log("MAPBIOMAS ALERTA - CLIENTE API OFICIAL V2")
            log("=" * 60)
            
            # Verificar credenciais
            if not EMAIL or not PASSWORD:
                log("\n⚠️  ATENCAO: Configure MAPBIOMAS_EMAIL e MAPBIOMAS_PASSWORD no ambiente.")
                return
            
            # 1. Autenticar
            log("\n[1/3] Autenticando na API...")
            token = sign_in(EMAIL, PASSWORD)
            log("✅ Autenticação bem-sucedida!")
            
            # 2. Carregar leads
            log("\n[2/3] Carregando leads da Lista Diamante...")
            leads = read_leads()
            log(f"✅ {len(leads)} leads com tese de NULIDADE encontrados.")
            
            # 3. Processar (pula automaticamente os já processados no CSV)
            log("\n[3/3] Processando via API...")
            results = process_leads(token, leads, limit=None, skip_processed=True)
            
            # 4. Auditoria de Qualidade
            investigate_final_quality()
            
            # Resumo final
            log("\n" + "=" * 60)
            log("RESUMO FINAL - PROCESSAMENTO CONCLUÍDO")
            log("=" * 60)
            break # Sai do loop se terminar tudo com sucesso
            
        except Exception as e:
            log(f"\n❌ ERRO DURANTE O PROCESSAMENTO: {e}")
            log("Reiniciando em 60 segundos para continuar de onde parou...")
            time.sleep(60)

if __name__ == "__main__":
    main()
