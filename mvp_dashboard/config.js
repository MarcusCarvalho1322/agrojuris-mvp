// Configuração da API baseada no ambiente
const getApiBaseUrl = () => {
  // Prioridade: variável de ambiente > modo de produção > localhost
  // Para usar variáveis de ambiente em produção, configure no Railway:
  // REACT_APP_API_BASE_URL=https://agrojuris-mvp-production.up.railway.app
  
  // Em um ambiente com build process (Vite, Webpack, etc), as variáveis seriam injetadas aqui
  // Por enquanto, detectamos baseado no hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // Se estiver rodando em produção (Railway, Vercel, etc)
    if (hostname !== 'localhost' && hostname !== '127.0.0.1' && hostname !== '') {
      return 'https://agrojuris-mvp-production.up.railway.app';
    }
  }
  
  // Desenvolvimento local
  return 'http://localhost:8000';
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),
  // Outras configurações podem ser adicionadas aqui
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
};

// Log da configuração atual (apenas em desenvolvimento)
if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
  console.log('🔧 Configuração atual:', CONFIG);
}
