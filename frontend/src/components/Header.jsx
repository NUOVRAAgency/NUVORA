import React, { useState } from "react";
import { Menu, Globe, X } from "lucide-react";
import { useLang } from "../contexts/LangContext";
import { useSettings } from "../contexts/SettingsContext";
import DrawerMenu from "./DrawerMenu";

export default function Header() {
  const { lang, toggle, t } = useLang();
  const { settings, logoUrl } = useSettings();
  const [open, setOpen] = useState(false);
  const [logoBroken, setLogoBroken] = useState(false);
  const showLogo = !!logoUrl && !logoBroken;

  return (
    <>
      <header
        data-testid="site-header"
        className="fixed top-0 inset-x-0 z-50 bg-[#E6F2F5]/85 backdrop-blur-xl border-b border-[#D7E6E9]"
      >
        <div className="mx-auto max-w-7xl px-5 md:px-10 h-16 md:h-20 flex items-center justify-between">
          {/* In RTL, "right" appears at the start. Logo at the start side per problem statement (Right side in RTL) */}
          <a href="/" className="flex items-center gap-3" data-testid="brand-logo-link">
            {showLogo ? (
              <img src={logoUrl} alt={settings.agency_name} className="h-9 md:h-10 w-auto" onError={() => setLogoBroken(true)} />
            ) : (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-9 h-9 md:w-10 md:h-10 rounded-xl bg-[#0A3D42] text-white font-display text-lg shadow-md">N</span>
                <span className="font-display text-xl md:text-2xl text-[#112325] tracking-tight" data-testid="brand-name">{settings.agency_name || "NUVORA"}</span>
              </div>
            )}
          </a>

          <div className="flex items-center gap-2 md:gap-3">
            <button
              data-testid="lang-toggle-btn"
              onClick={toggle}
              className="btn-3d btn-3d-light bg-white text-[#112325] px-3 md:px-4 h-10 md:h-11 rounded-xl inline-flex items-center gap-2 font-semibold"
              aria-label="Toggle language"
            >
              <Globe className="w-4 h-4" />
              <span className="text-sm">{lang === "ar" ? "EN" : "AR"}</span>
            </button>

            <button
              data-testid="menu-open-btn"
              onClick={() => setOpen(true)}
              className="btn-3d btn-3d-light bg-white text-[#112325] w-10 h-10 md:w-11 md:h-11 rounded-xl inline-flex items-center justify-center"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <DrawerMenu open={open} onClose={() => setOpen(false)} />
    </>
  );
}
