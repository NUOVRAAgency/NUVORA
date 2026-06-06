import React from "react";
import { useLang } from "../contexts/LangContext";
import { useSettings } from "../contexts/SettingsContext";

export default function Footer() {
  const { t } = useLang();
  const { settings } = useSettings();
  return (
    <footer data-testid="site-footer" className="bg-[#0A3D42] text-white">
      <div className="mx-auto max-w-7xl px-5 md:px-10 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <div>
            <span className="font-display text-3xl">{settings.agency_name || "mergent"}</span>
            <p className="mt-3 text-white/70 max-w-sm leading-relaxed">{t.footer.tag}</p>
          </div>
          <div>
            <div className="text-white/60 text-sm uppercase tracking-widest mb-3">{t.nav.home}</div>
            <ul className="space-y-2 text-white/90">
              <li><a href="#home" className="hover:text-[#5EEAD4] transition-colors" data-testid="footer-link-home">{t.nav.home}</a></li>
              <li><a href="#work" className="hover:text-[#5EEAD4] transition-colors" data-testid="footer-link-work">{t.nav.work}</a></li>
              <li><a href="#consult" className="hover:text-[#5EEAD4] transition-colors" data-testid="footer-link-consult">{t.nav.consult}</a></li>
              <li><a href="#contact" className="hover:text-[#5EEAD4] transition-colors" data-testid="footer-link-contact">{t.nav.contact}</a></li>
            </ul>
          </div>
          <div>
            <div className="text-white/60 text-sm uppercase tracking-widest mb-3">{t.contact.title}</div>
            <ul className="space-y-2 text-white/90" dir="ltr">
              <li>{settings.phone}</li>
              <li>{settings.email}</li>
            </ul>
          </div>
        </div>
        <div className="mt-12 border-t border-white/10 pt-6 text-white/60 text-sm text-center">
          {t.footer.copy}
        </div>
      </div>
    </footer>
  );
}
