import React from "react";
import { Phone, Mail, MessageCircle } from "lucide-react";
import { useLang } from "../contexts/LangContext";
import { useSettings } from "../contexts/SettingsContext";

export default function Footer() {
  const { t } = useLang();
  const { settings } = useSettings();
  const telHref = `tel:${(settings.phone || "").replace(/[^\d+]/g, "")}`;
  const mailHref = `mailto:${settings.email || ""}`;
  const waHref = `https://wa.me/${(settings.whatsapp || "").replace(/[^\d]/g, "")}`;

  return (
    <footer data-testid="site-footer" className="bg-[#0A3D42] text-white">
      <div className="mx-auto max-w-7xl px-5 md:px-10 pt-14 pb-6">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-10">
          <div>
            <span className="font-display text-3xl tracking-tight">{settings.agency_name || "NUVORA"}</span>
            <p className="mt-3 text-white/70 max-w-sm leading-relaxed text-sm">{t.footer.tag}</p>
          </div>
          <ul className="flex flex-col gap-3 text-sm">
            <li>
              <a
                data-testid="footer-tel-link"
                href={telHref}
                className="inline-flex items-center gap-2.5 text-white/85 hover:text-[#5EEAD4] transition-colors"
                dir="ltr"
              >
                <Phone className="w-4 h-4 opacity-80" />
                <span className="font-medium">{settings.phone}</span>
              </a>
            </li>
            <li>
              <a
                data-testid="footer-mail-link"
                href={mailHref}
                className="inline-flex items-center gap-2.5 text-white/85 hover:text-[#5EEAD4] transition-colors"
                dir="ltr"
              >
                <Mail className="w-4 h-4 opacity-80" />
                <span className="font-medium">{settings.email}</span>
              </a>
            </li>
            <li>
              <a
                data-testid="footer-wa-link"
                href={waHref}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2.5 text-white/85 hover:text-[#5EEAD4] transition-colors"
              >
                <MessageCircle className="w-4 h-4 opacity-80" />
                <span className="font-medium">{t.contact.supportTitle}</span>
              </a>
            </li>
          </ul>
        </div>
        <div className="mt-10 border-t border-white/10 pt-4 text-center">
          <p className="text-[11px] leading-tight tracking-wide text-white/55" data-testid="footer-copy">{t.footer.copy}</p>
        </div>
      </div>
    </footer>
  );
}
