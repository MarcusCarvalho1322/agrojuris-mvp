# MVP SETUP - PASSO A PASSO

## 1) Criar banco no Neon
1. Crie um projeto Postgres no Neon.
2. Copie a DATABASE_URL (connection string).

## 2) Rodar backend local (teste)
1. Entre na pasta mvp_backend.
2. Crie um .env com DATABASE_URL.
3. Instale dependencias:
   pip install -r requirements.txt
4. Carregue os dados:
   python load_from_csv.py
5. Suba a API:
   uvicorn app:app --reload

## 3) Deploy no Railway
1. Crie um novo projeto Railway.
2. Conecte o repo.
3. Configure a variavel DATABASE_URL (Neon).
4. Comando de start:
   uvicorn app:app --host 0.0.0.0 --port 8000

## 4) Deploy do dashboard (Vercel)
1. Hospede a pasta mvp_dashboard como site estatico.
2. Edite mvp_dashboard/config.js e ajuste API_BASE_URL para a URL do Railway.

## 5) Atualizacao diaria (GitHub Actions)
1. Crie um workflow com cron diario.
2. Execute python mvp_backend/load_from_csv.py.

## Observacoes
- O MVP usa CSVs locais para alimentar o banco.
- Depois substituimos por ETL direto das APIs.
