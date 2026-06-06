import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { tFor } from "../i18n";

const LangContext = createContext(null);

const ARABIC_REGIONS = [
  "ar", "ae", "sa", "kw", "qa", "bh", "om", "eg", "iq", "jo", "lb", "sy", "ye", "ly", "tn", "dz", "ma", "sd", "mr", "ps"
];

const detectBrowserLang = () => {
  if (typeof navigator === "undefined") return "ar";
  const candidates = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "ar"])
    .map((x) => (x || "").toLowerCase());
  for (const c of candidates) {
    if (c.startsWith("ar")) return "ar";
    const region = c.split("-")[1];
    if (region && ARABIC_REGIONS.includes(region)) return "ar";
  }
  return "en";
};

export const LangProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("mergent_lang");
    if (saved === "ar" || saved === "en") return saved;
    return detectBrowserLang();
  });
  const [manualOverride, setManualOverride] = useState(() => !!localStorage.getItem("mergent_lang"));

  useEffect(() => {
    if (manualOverride) localStorage.setItem("mergent_lang", lang);
    const dir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
  }, [lang, manualOverride]);

  const setLangManual = (next) => { setManualOverride(true); setLang(next); };
  const toggle = () => setLangManual(lang === "ar" ? "en" : "ar");

  const value = useMemo(() => ({
    lang, setLang: setLangManual, toggle, t: tFor(lang), dir: lang === "ar" ? "rtl" : "ltr",
  }), [lang]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
};

export const useLang = () => useContext(LangContext);
