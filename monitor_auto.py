"""
Monitor e Reiniciador Automático - MapBiomas API
Verifica a cada 5 minutos se o processo está rodando.
Se tiver parado, reinicia automaticamente.
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime

SCRIPT_PATH = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\mapbiomas_api_client.py"
LOG_FILE = r"c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\log_monitor.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def process_running():
    """Verifica se há processo Python rodando com mapbiomas_api_client"""
    result = subprocess.run(
        "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*mapbiomas*' }",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0 and "python" in result.stdout.lower()

def start_process():
    """Inicia o processo em background"""
    subprocess.Popen(
        ["python", SCRIPT_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    log("✅ Processo iniciado")

def main():
    log("=" * 60)
    log("MONITOR E REINICIADOR AUTOMÁTICO - MAPBIOMAS API")
    log("=" * 60)
    log("Verificando a cada 5 minutos...")
    
    while True:
        try:
            if not process_running():
                log("⚠️  Processo não detectado! Reiniciando...")
                start_process()
                time.sleep(10)
            else:
                log("✅ Processo rodando normalmente")
            
            time.sleep(300)  # 5 minutos
        
        except Exception as e:
            log(f"❌ Erro no monitor: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
