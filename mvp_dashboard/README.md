# Agrojuris MVP

Agrojuris Dashboard Intelligence

## 🔧 Configuração

### Variáveis de Ambiente

Este dashboard é um site estático que detecta automaticamente o ambiente baseado no hostname:
- **localhost/127.0.0.1**: usa `http://localhost:8000`
- **Outros domínios** (produção): usa `https://agrojuris-mvp-production.up.railway.app`

Para desenvolvimento local:
1. O backend deve estar rodando em `http://localhost:8000`
2. Abra `index.html` em um servidor HTTP local

Para produção (Railway/Vercel):
1. Faça deploy da pasta `mvp_dashboard`
2. A configuração detectará automaticamente que está em produção

### Arquivos de Configuração

Os arquivos `.env.development` e `.env.production` servem como referência e documentação das URLs esperadas em cada ambiente. Em um projeto com build process (Vite, Webpack, Create React App), esses arquivos seriam usados automaticamente.

## 🚀 Como executar

### Desenvolvimento

```bash
# Opção 1: Servidor Python
cd mvp_dashboard
python3 -m http.server 3000

# Opção 2: Servidor Node.js (se tiver npx)
cd mvp_dashboard
npx serve .

# Acesse: http://localhost:3000
```

### Produção

Faça deploy da pasta `mvp_dashboard` em:
- Vercel (sites estáticos)
- Railway (sites estáticos)
- Netlify
- GitHub Pages
- Qualquer host de arquivos estáticos

## 📦 Estrutura

```
mvp_dashboard/
├── config.js          # Configurações da aplicação (detecção automática)
├── app.js             # Lógica principal do dashboard
├── index.html         # Página principal
├── styles.css         # Estilos
├── services/
│   └── api.js        # Serviço HTTP reutilizável (opcional)
└── assets/           # Recursos estáticos
```

## 📝 Usando o ApiService

Para usar o serviço HTTP reutilizável em novos recursos:

```html
<!-- No HTML, adicione após config.js -->
<script src="config.js"></script>
<script src="services/api.js"></script>
<script>
  // Usar o apiService
  apiService.get('/leads').then(data => {
    console.log('Leads:', data);
  });
</script>
```

## Setup Original

1. Edite config.js e ajuste API_BASE_URL.
2. Hospede a pasta como site estatico (Vercel).
