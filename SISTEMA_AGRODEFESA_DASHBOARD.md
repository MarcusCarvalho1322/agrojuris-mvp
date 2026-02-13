# MANUAL DO OPERADOR: SISTEMA DE INTELIGÊNCIA AGRODEFESA

Você agora tem o controle total da "Máquina de Captura" de leads milionários. Abaixo, as instruções para gerenciar o sistema que acabei de configurar.

---

## 1. COMPONENTES DO SISTEMA
O sistema é composto por 3 engrenagens trabalhando em cadeia:

1.  **Pipeline de Dados (`analise_inteligencia.py`):**
    *   Lê os 52 mil leads, cruza com crédito rural e separa os 2.773 **Diamantes**.
    *   Identifica os 2.074 casos de **Nulidade por Satélite**.
    *   Extrai Latitude e Longitude exatas de cada multa.

2.  **Motor de Captura (`mapbiomas_automation.py`):**
    *   Acessa o MapBiomas Alerta automaticamente.
    *   Vira para a coordenada da fazenda, aplica filtros e **baixa o PDF do laudo**.
    *   Salva tudo na pasta `_mapbiomas_reports/`.

3.  **Dossiê Comercial (`CASO_ESTUDO_EMERSON_50M.md`):**
    *   Modelo de como transformar esses dados em um "vídeo-presente" que fecha o contrato.

---

## 2. COMO EXECUTAR (O Passo a Passo)

### Passo 1: Preparar o Ambiente (Apenas 1 vez)
Abra o terminal e execute:
```powershell
pip install playwright
python -m playwright install chromium
```

### Passo 2: O Login "Mestre"
O MapBiomas exige login. Na primeira vez que você rodar o sistema, ele vai abrir o Chrome. **Você deve fazer o login manualmente**. Depois que você fechar o Chrome, o sistema vai lembrar de você para sempre (salvamos os cookies na pasta `_mapbiomas_profile`).

### Passo 3: Disparar em Lote
Para começar a baixar os primeiros 10 laudos Diamante (piloto):
```powershell
python mapbiomas_automation.py
```

---

## 3. GESTÃO DOS RESULTADOS
Acompanhe os resultados em tempo real:
*   **Logs:** Abra o arquivo `execucao_mapbiomas.log` para ver quais leads foram processados com sucesso.
*   **Relatórios:** Vá na pasta `_mapbiomas_reports/`. Cada PDF lá dentro é um contrato em potencial.

---

## 4. PRÓXIMAS EVOLUÇÕES (Sua Gestão)
O sistema está em "Piloto". Como seu gestor de IA, recomendo:
1.  **Aumentar o Lote:** Mudar no código de `leads[:10]` para `leads[:100]` após validar os primeiros.
2.  **Módulo de IA (Lote 2):** Criar o script que lê o PDF baixado e escreve o texto do e-mail de abordagem personalizado.
3.  **CRM Automático:** Disparar o link do vídeo do Loom via API de WhatsApp (opcional).

O sistema está **ativado e pronto para o primeiro run**.
Deseja que eu faça algum ajuste fino em algum seletor ou podemos rodar o piloto?
