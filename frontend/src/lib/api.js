import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const TOKEN_KEY = "mergent_token";

export const setToken = (t) => {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
};
export const getToken = () => localStorage.getItem(TOKEN_KEY);

const api = axios.create({
  baseURL: API,
});

api.interceptors.request.use((cfg) => {
  const t = getToken();
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export default api;

// Helper: convert relative image URL from backend to absolute one
export const absUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${BACKEND_URL}${path}`;
};
