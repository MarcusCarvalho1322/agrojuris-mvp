@echo off
setlocal enabledelayedexpansion

REM Dashboard de progresso do MapBiomas API

:loop
cls
echo ================================================================
echo   MAPBIOMAS API - DASHBOARD DE PROGRESSO
echo ================================================================
echo.

REM Verificar se processo Python está rodando
tasklist | find "python.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] Processo Python ativo
) else (
    echo [AGUARDANDO] Processo Python
)

echo.
echo ================================================================
echo   ÚLTIMAS ATIVIDADES:
echo ================================================================
powershell -Command "Get-Content 'c:\Users\Marcus Carvalho PC\Documents\AgroDefesa_Dossie\log_api_mapbiomas.txt' -Tail 10"

echo.
echo ================================================================
echo   PRÓXIMA ATUALIZAÇÃO EM 5 MINUTOS... (Feche esta janela para sair)
echo ================================================================

timeout /t 300 /nobreak

goto loop
