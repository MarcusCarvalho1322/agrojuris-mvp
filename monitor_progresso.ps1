# Monitor do Processamento MapBiomas
# Atualiza a cada 30 segundos com progresso

$LogFile = "c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\log_api_mapbiomas.txt"
$CSVFile = "c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\RELATORIO_MAPBIOMAS_API.csv"

while ($true) {
    Clear-Host
    Write-Host "============================================================"
    Write-Host "MONITOR DE PROGRESSO - MAPBIOMAS API"
    Write-Host "============================================================"
    Write-Host ""
    
    # Verificar processo
    $proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*mapbiomas_api_client*" } | Select-Object -First 1
    
    if ($proc) {
        Write-Host "✅ PROCESSO ATIVO (PID: $($proc.Id))"
        Write-Host "   CPU: $($proc.CPU.ToString('F1')) segundos"
        Write-Host "   Memória: $([math]::Round($proc.WS/1MB, 1)) MB"
    } else {
        Write-Host "❌ PROCESSO NÃO ESTÁ RODANDO"
    }
    
    Write-Host ""
    
    # Últimas linhas do log
    $lastLines = Get-Content $LogFile -Tail 10 -ErrorAction SilentlyContinue
    if ($lastLines) {
        Write-Host "ÚLTIMAS ATIVIDADES:"
        $lastLines | ForEach-Object { Write-Host "  $_" }
    }
    
    Write-Host ""
    
    # Análise do CSV
    if (Test-Path $CSVFile) {
        $csv = Import-Csv -Path $CSVFile -Delimiter ";"
        $status_summary = $csv | Group-Object STATUS_IA | Select-Object Name, Count | Sort-Object Count -Descending
        
        Write-Host "RESUMO DO RELATÓRIO:"
        Write-Host "  Total linhas: $($csv.Count)"
        $status_summary | ForEach-Object { 
            Write-Host "  - $($_.Name): $($_.Count)"
        }
    }
    
    Write-Host ""
    Write-Host "Próxima atualização em 30 segundos... (Pressione Ctrl+C para sair)"
    Start-Sleep -Seconds 30
}
