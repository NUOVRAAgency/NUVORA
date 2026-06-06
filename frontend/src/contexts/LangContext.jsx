import React, { createContext, useContext, useEffect, useState } from "react";
import { tFor } from "../i18n";

const LangContext = createContext(null);

export const LangProvider = ({ children }) => {
  const [lang, setLang] = useState(() => localStorage.getItem("mergent_lang") || "ar");
  useEffect(() => {
    localStorage.setItem("mergent_lang", lang);
    const dir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
  }, [lang]);
  const toggle = () => setLang((l) => (l === "ar" ? "en" : "ar"));
  return (
    <LangContext.Provider value={{ lang, setLang, toggle, t: tFor(lang), dir: lang === "ar" ? "rtl" : "ltr" }}>
      {children}
    </LangContext.Provider>
  );
};

export const useLang = () => useContext(LangContext);
