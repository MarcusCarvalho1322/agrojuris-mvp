// Configuração da API baseada no ambiente
const getApiBaseUrl = () => {
  // Prioridade: variável de ambiente > modo de produção > localhost
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  
  if (process.env.NODE_ENV === 'production') {
    return 'https://agrojuris-mvp-production.up.railway.app';
  }
  
  return 'http://localhost:8000';
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),
  // Outras configurações podem ser adicionadas aqui
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
};

// Log da configuração atual (apenas em desenvolvimento)
if (process.env.NODE_ENV !== 'production') {
  console.log('🔧 Configuração atual:', CONFIG);
}

export default CONFIG;
