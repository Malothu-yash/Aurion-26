// Environment configuration for frontend
// This centralizes all environment variable access

export const ENV = {
  // API URLs
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000',
  
  // Derived URLs
  get AUTH_BASE() {
    return `${this.API_BASE_URL}/auth`;
  },
  
  get ADMIN_BASE() {
    return `${this.API_BASE_URL}/admin`;
  },
  
  get CHAT_STREAM() {
    return `${this.API_BASE_URL}/chat/stream`;
  },
  
  get MINI_AGENT_STREAM() {
    return `${this.API_BASE_URL}/mini_agent/stream`;
  },
  
  get HIGHLIGHTS_BASE() {
    return `${this.API_BASE_URL}/highlights`;
  },
  
  get MINI_AGENT_SESSIONS() {
    return `${this.API_BASE_URL}/mini-agent-sessions`;
  },
  
  // Development mode
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};

// Validate required environment variables
if (!ENV.API_BASE_URL) {
  console.warn('⚠️ VITE_API_BASE_URL not set, using default localhost');
}

// Log configuration in development
if (ENV.isDevelopment) {
  console.log('🔧 Environment Configuration:');
  console.log('  API_BASE_URL:', ENV.API_BASE_URL);
  console.log('  BACKEND_URL:', ENV.BACKEND_URL);
}
