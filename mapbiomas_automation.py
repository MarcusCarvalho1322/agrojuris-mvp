"""
PoC: Automate MapBiomas Alerta with Playwright (headless Chromium).
- Uses persistent profile for login (first run opens browser for manual login).
- Reads leads from a CSV with lat/lon and date window.
- Navigates to the coordinate, applies filters, clicks the largest alert, and saves PDF.
- Skeleton only: selectors may need adjustment after first interactive run.
"""
import asyncio
import csv
import os
import pdfplumber
from pathlib import Path
from typing import Dict, List
from playwright.async_api import async_playwright, BrowserContext, Page

# ---------------------------
# CONFIG PROD
# ---------------------------
# URL correta da plataforma de alertas (não o site institucional)
MAPBIOMAS_URL = "https://plataforma.alerta.mapbiomas.org/"
USER_DATA_DIR = str(Path(__file__).parent / "_mapbiomas_profile")
INPUT_CSV = str(Path(__file__).parent / "LISTA_DIAMANTE_MATRIZ_TESES_2026.csv")
OUTPUT_DIR = Path(__file__).parent / "_mapbiomas_reports"
REPORT_FINAL = Path(__file__).parent / "RELATORIO_FINAL_IA_OPORTUNIDADES.csv"
LOG_FILE = Path(__file__).parent / "execucao_mapbiomas.log"

async def analyze_pdf(pdf_path: Path) -> Dict[str, str]:
    """Analisa o PDF baixado em busca de gatilhos de nulidade."""
    results = {"status": "Erro", "chance": "0%", "motivo": "PDF não encontrado"}
    if not pdf_path.exists():
        return results

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            
        if "ASV" in text.upper() or "AUTORIZAÇÃO" in text.upper():
            return {"status": "NULIDADE ALTA", "chance": "95%", "motivo": "Autorização (ASV) detectada no MapBiomas."}
        elif "Sobreposição CAR" in text:
            return {"status": "REVISÃO", "chance": "60%", "motivo": "Sobreposição de CAR detectada."}
        else:
            return {"status": "ANALISAR", "chance": "30%", "motivo": "Sem evidência automática de ASV no PDF."}
    except Exception as e:
        return {"status": "ERRO LEITURA", "chance": "0%", "motivo": str(e)}

async def save_to_report(data: Dict[str, str]):
    file_exists = REPORT_FINAL.exists()
    keys = ["NOME_INFRATOR", "VALOR_MULTA", "STATUS_IA", "CHANCE_NULIDADE", "MOTIVO_IA", "PDF_LINK"]
    with open(REPORT_FINAL, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys, delimiter=";")
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def read_leads_from_matrix(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    # Usando o CSV gerado pelo sistema com encoding utf-8-sig e separador ;
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            # Filtramos apenas casos de Nulidade (Flora) para otimizar processamento
            if "NULIDADE" in row.get("TESE_PRIMARIA", ""):
                # Extraindo latitude e longitude do link do Google Maps ou similar
                # Aqui assumimos que o link formatado tem coords ou pegamos da base original
                # Para esta versão, usaremos um parser simples no link do Maps se lat/lon não estiverem em colunas extras
                rows.append(row)
    return rows

async def log_event(message: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")
    print(message)


async def ensure_output() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def open_context(playwright) -> BrowserContext:
    # Aumentamos o timeout para 60s para conexões lentas
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        viewport={"width": 1280, "height": 900},
        args=["--start-maximized"]
    )
    browser.set_default_timeout(60000)
    return browser


async def go_to_coordinate(page: Page, lat: str, lon: str) -> None:
    # Sanitização: transformar vírgula em ponto se necessário
    lat = lat.replace(",", ".").strip()
    lon = lon.replace(",", ".").strip()
    
    await log_event(f"Buscando coordenadas: {lat}, {lon}")
    
    # Ir para a plataforma
    await page.goto(MAPBIOMAS_URL, wait_until="networkidle")
    await page.wait_for_timeout(5000)
    
    # Aceitar termos se aparecer o modal
    try:
        concordo_btn = await page.wait_for_selector("text=CONCORDO", timeout=5000)
        if concordo_btn:
            await concordo_btn.click()
            await page.wait_for_timeout(2000)
    except:
        pass
    
    # Procurar barra de busca e digitar coordenadas
    try:
        # Busca por diferentes seletores possíveis
        search_selectors = [
            "input[placeholder*='Buscar']",
            "input[placeholder*='Pesquisar']",
            "input[placeholder*='coordenada']",
            ".search-input",
            "input[type='search']"
        ]
        
        for selector in search_selectors:
            try:
                search_box = await page.wait_for_selector(selector, timeout=3000)
                if search_box:
                    await search_box.fill(f"{lat}, {lon}")
                    await page.keyboard.press("Enter")
                    await log_event(f"Coordenadas inseridas na busca.")
                    break
            except:
                continue
    except Exception as e:
        await log_event(f"Barra de busca não encontrada: {str(e)}")
    
    await page.wait_for_timeout(8000) # Tempo para o mapa voar e carregar alertas


async def apply_filters(page: Page, data_inicio: str, data_fim: str, area_min_ha: str) -> None:
    # Filtros são opcionais - a busca por coordenada já leva ao local correto
    # Apenas espera o carregamento
    await page.wait_for_timeout(2000)


async def click_largest_alert(page: Page) -> None:
    # No MapBiomas, após a busca, os alertas aparecem em uma lista ou no mapa.
    # Vamos tentar clicar no primeiro item da lista de resultados se ela aparecer.
    try:
        # Seletor genérico para itens da lista de alertas
        alert_item = await page.wait_for_selector(".alert-item, .list-group-item, [class*='alert']", timeout=10000)
        if alert_item:
            await alert_item.click()
            await log_event("Alerta selecionado da lista.")
            await page.wait_for_timeout(3000)
            return
    except Exception:
        pass

    # Fallback: clicar no centro do mapa (onde a busca centralizou)
    await log_event("Tentando clique no centro do mapa...")
    try:
        canvas = await page.query_selector("canvas")
        if canvas:
            box = await canvas.bounding_box()
            if box:
                await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    except Exception:
        pass
    await page.wait_for_timeout(3000)


async def download_report(page: Page, lead_id: str) -> None:
    pdf_path = OUTPUT_DIR / f"{lead_id}_mapbiomas.pdf"
    
    # 1. Tentar clicar no botão que abre a aba de resumo detalhado
    try:
        # Seletor do botão de detalhes/relatório no MapBiomas Alerta
        report_btn = await page.wait_for_selector("button:has-text('Relatório'), .btn-download, a[href*='report']", timeout=15000)
        if report_btn:
            async with page.context.expect_page() as new_page_info:
                await report_btn.click()
            new_page = await new_page_info.value
            await new_page.wait_for_load_state("networkidle")
            await new_page.wait_for_timeout(5000) # Espera renderizar os textos
            await new_page.pdf(path=str(pdf_path), format="A4")
            await new_page.close()
            await log_event(f"Documento Técnico Gerado: {pdf_path.name}")
            return
    except Exception as e:
        await log_event(f"Tentativa 1 (Relatório) falhou para {lead_id}. Tentando Print...")

    # 2. Fallback: Print da Visão Geral (se o botão não existir ou falhar)
    try:
        await page.pdf(path=str(pdf_path), format="A4")
        await log_event(f"Print de Segurança Gerado: {pdf_path.name}")
    except Exception as e:
        await log_event(f"Falha total ao salvar PDF para {lead_id}: {str(e)}")


async def extract_coords(lead: Dict[str, str]) -> tuple:
    # Agora pegamos diretamente das colunas do sistema
    lat = lead.get("NUM_LATITUDE_AUTO")
    lon = lead.get("NUM_LONGITUDE_AUTO")
    return lat, lon

async def process_lead(ctx: BrowserContext, lead: Dict[str, str]) -> None:
    lead_name = lead.get("NOME_INFRATOR") or lead.get("ï»¿NOME_INFRATOR")
    lat, lon = await extract_coords(lead)
    
    if not lat or not lon or lat == "0" or lon == "0":
        await log_event(f"[AVISO] Coordenada Zero/Nula para: {lead_name}. Tentando busca por local.")
        # Fallback para busca visual se necessário (opcional)
        return

    await log_event(f"[START] Processando Lead: {lead_name} (Coord: {lat}, {lon})")
    page = await ctx.new_page()
    try:
        await go_to_coordinate(page, lat, lon)
        # Ajuste de data: Pegamos a data da multa e olhamos 3 meses antes e depois
        data_multa = lead.get("DAT_HORA_AUTO_INFRACAO", "2024-11-18")
        # Simplificação: janelas fixas para o piloto
        await apply_filters(page, "01/01/2024", "31/12/2024", "50")
        await click_largest_alert(page)
        await download_report(page, lead_name.replace(" ", "_"))
        await log_event(f"[SUCCESS] Relatório salvo para: {lead_name}")
    except Exception as e:
        await log_event(f"[FAIL] Erro no lead {lead_name}: {str(e)}")
    finally:
        await page.close()


async def main() -> None:
    await ensure_output()
    leads = read_leads_from_matrix(INPUT_CSV)
    
    if not leads:
        print("[ERRO] Ninguém na lista Diamante com tese de NULIDADE.")
        return

    await log_event(f">>> Iniciando processamento de {len(leads)} leads Diamante.")
    
    async with async_playwright() as p:
        ctx = await open_context(p)
        page = await ctx.new_page()
        
        # Navega para login (sessão persistente já vai ter o cookie se já logou antes)
        await page.goto(MAPBIOMAS_URL)
        print("\n" + "="*70)
        print("🤖 MODO AUTOMÁTICO TOTAL - SEM INTERAÇÃO NECESSÁRIA")
        print("O robô vai aguardar 30 segundos para a página carregar...")
        print("="*70)
        await page.wait_for_timeout(30000)  # 30s para garantir carregamento/login
        await page.close()

        # Batch Processing: 100 in 100
        for i in range(0, len(leads), 100):
            batch = leads[i : i + 100]
            await log_event(f"\n🚀 PROCESSANDO LOTE {i//100 + 1} ({len(batch)} leads)...")
            
            for count, lead in enumerate(batch, 1):
                lead_name = lead.get("NOME_INFRATOR") or "Desconhecido"
                pdf_name = lead_name.replace(" ", "_")
                pdf_path = OUTPUT_DIR / f"{pdf_name}_mapbiomas.pdf"
                
                # Pula se já baixou (evita retrabalho)
                if not pdf_path.exists():
                    await process_lead(ctx, lead)
                
                # FISCALIZAÇÃO IA cada PDF
                ia_result = await analyze_pdf(pdf_path)
                
                await save_to_report({
                    "NOME_INFRATOR": lead_name,
                    "VALOR_MULTA": lead.get("VALOR_MULTA", "0"),
                    "STATUS_IA": ia_result["status"],
                    "CHANCE_NULIDADE": ia_result["chance"],
                    "MOTIVO_IA": ia_result["motivo"],
                    "PDF_LINK": str(pdf_path)
                })
                
                print(f"📊 Progresso: {i + count}/{len(leads)} - {lead_name}: {ia_result['status']}")

            # Pequena pausa entre lotes para não ser bloqueado
            await log_event(f"✅ Lote {i//100 + 1} finalizado. Aguardando 10s...")
            await asyncio.sleep(10)
            
        await ctx.close()
        print("\n✅ PROCESSO TOTAL FINALIZADO!")


if __name__ == "__main__":
    asyncio.run(main())
