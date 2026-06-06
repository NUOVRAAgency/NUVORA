import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { setToken, getToken } from "../lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  const fetchMe = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setChecking(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    setToken(data.access_token);
    setUser({ id: data.id, email: data.email, role: data.role });
    return data;
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, checking, fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
