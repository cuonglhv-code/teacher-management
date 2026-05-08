import axios from 'axios';

// Use environment variable for API base URL (for Vercel deployment)
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const client = axios.create({
  baseURL: `${API_BASE}/api/v1`,
});

export default client;