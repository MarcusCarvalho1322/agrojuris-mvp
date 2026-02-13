// API configuration based on environment
const getApiBaseUrl = () => {
  // Priority: production hostname mapping > localhost
  
  // In an environment with build process (Vite, Webpack, etc), variables would be injected here
  // For now, we detect based on hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If running in production (Vercel, etc)
    if (hostname !== 'localhost' && hostname !== '127.0.0.1' && hostname !== '') {
      return 'https://web-production-77c2.up.railway.app';
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
