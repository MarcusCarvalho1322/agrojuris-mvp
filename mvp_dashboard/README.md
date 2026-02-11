# Agrojuris MVP

Agrojuris Dashboard Intelligence

## 🔧 Configuração

### Variáveis de Ambiente

1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Configure sua URL da API no arquivo `.env`:
   ```env
   REACT_APP_API_BASE_URL=http://localhost:8000
   ```

### Ambientes

- **Desenvolvimento**: usa `.env.development` ou `http://localhost:8000`
- **Produção**: usa `.env.production` ou a URL do Railway

### Railway Configuration

No painel do Railway, adicione a variável de ambiente:
```
REACT_APP_API_BASE_URL=https://agrojuris-mvp-production.up.railway.app
```

## 🚀 Como executar

```bash
# Desenvolvimento
npm run dev

# Produção
npm run build
npm start
```

## 📦 Estrutura

```
mvp_dashboard/
├── config.js          # Configurações da aplicação
├── services/
│   └── api.js        # Serviço HTTP reutilizável
├── .env.development  # Variáveis de desenvolvimento
├── .env.production   # Variáveis de produção
└── .env.example      # Exemplo de configuração
```

## Setup Original

1. Edite config.js e ajuste API_BASE_URL.
2. Hospede a pasta como site estatico (Vercel).
