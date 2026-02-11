// API configuration based on environment
const getApiBaseUrl = () => {
  // Priority: environment variable > production mode > localhost
  // To use environment variables in production, configure in Railway:
  // REACT_APP_API_BASE_URL=https://agrojuris-mvp-production.up.railway.app
  
  // In an environment with build process (Vite, Webpack, etc), variables would be injected here
  // For now, we detect based on hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If running in production (Railway, Vercel, etc)
    if (hostname !== 'localhost' && hostname !== '127.0.0.1' && hostname !== '') {
      return 'https://agrojuris-mvp-production.up.railway.app';
    }
  }
  
  // Local development
  return 'http://localhost:8000';
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),
  // Additional configurations for future use
  TIMEOUT: 10000,        // Request timeout in milliseconds (for future implementation)
  RETRY_ATTEMPTS: 3,     // Number of retry attempts (for future implementation)
};

// Log current configuration (development only)
if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
  console.log('🔧 Current configuration:', CONFIG);
}
