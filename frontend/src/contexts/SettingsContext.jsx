import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { absUrl } from "../lib/api";

const SettingsContext = createContext(null);

const DEFAULTS = {
  agency_name: "mergent",
  phone: "+1 (608) 979-3938",
  whatsapp: "+16089793938",
  support_phone: "+1 (608) 979-3938",
  email: "nuvoranuvora760@gmail.com",
  logo_path: "",
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(DEFAULTS);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/settings");
      setSettings({ ...DEFAULTS, ...data });
    } catch (e) {
      // keep defaults
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const logoUrl = settings.logo_path ? absUrl(`/api/files/${settings.logo_path}`) : "";

  return (
    <SettingsContext.Provider value={{ settings, setSettings, refresh: load, loaded, logoUrl }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => useContext(SettingsContext);
