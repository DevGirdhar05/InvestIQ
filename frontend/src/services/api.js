const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
};

export const api = {
  // GET /analyze/{ticker}
  analyze: async (ticker) => {
    const response = await fetch(`${BASE_URL}/analyze/${ticker}`);
    return handleResponse(response);
  },

  // GET /explain/{ticker}
  explain: async (ticker) => {
    const response = await fetch(`${BASE_URL}/explain/${ticker}`);
    return handleResponse(response);
  },

  // GET /sentiment/{ticker}
  sentiment: async (ticker) => {
    const response = await fetch(`${BASE_URL}/sentiment/${ticker}`);
    return handleResponse(response);
  },

  // POST /ask
  ask: async (question, ticker = null) => {
    const response = await fetch(`${BASE_URL}/ask`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ question, ticker }),
    });
    return handleResponse(response);
  },

  // GET /overview
  overview: async () => {
    const response = await fetch(`${BASE_URL}/overview`);
    return handleResponse(response);
  },

  // GET /health
  health: async () => {
    const response = await fetch(`${BASE_URL}/health`);
    return handleResponse(response);
  },
};