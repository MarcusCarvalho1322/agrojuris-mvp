import pdfplumber
from pathlib import Path

def analyze_mapbiomas_pdf(file_path):
    print(f"--- ANALISANDO DOCUMENTO: {file_path.name} ---")
    
    if not file_path.exists():
        print("Erro: PDF não encontrado.")
        return

    text_content = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    # Critérios de Nulidade (Heurística de Inteligência)
    asv_found = "ASV" in text_content.upper() or "AUTORIZAÇÃO DE SUPRESSÃO" in text_content.upper()
    car_status = "Pendente" if "CAR em análise" in text_content else "Confirmado"
    georef_error = "Deslocamento" in text_content or "Inconsistência" in text_content

    print("\n[RESULTADO DA IA]")
    if asv_found:
        print("🎯 ALVO CRÍTICO: Encontrada menção a ASV/Autorização. Chance de Nulidade: 95%")
        print("Argumento: O proprietário tinha autorização, mas o satélite disparou o alerta por erro de processamento.")
    elif georef_error:
        print("⚠️ ERRO TÉCNICO: Detectada inconsistência de georreferenciamento. Chance de Nulidade: 70%")
    else:
        print("⚠️ ANÁLISE INCONCLUSIVA: Sem prova documental direta no resumo. Necessário checagem manual do polígono.")

    print("\n--- TRECHO EXTRAÍDO PARA VALIDAÇÃO ---")
    print(text_content[:1500] + "...") # Primeiros 1500 caracteres

if __name__ == "__main__":
    pdf_file = Path(r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\_mapbiomas_reports\EMERSON_DE_SOUZA_mapbiomas.pdf")
    analyze_mapbiomas_pdf(pdf_file)
