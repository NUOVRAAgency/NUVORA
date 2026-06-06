import React from "react";
import { Phone, Mail, Headphones } from "lucide-react";
import { useLang } from "../contexts/LangContext";
import { useSettings } from "../contexts/SettingsContext";

export default function Contact() {
  const { t } = useLang();
  const { settings } = useSettings();
  const telHref = `tel:${(settings.phone || "").replace(/[^\d+]/g, "")}`;
  const mailHref = `mailto:${settings.email || ""}`;
  const waHref = `https://wa.me/${(settings.whatsapp || "").replace(/[^\d]/g, "")}`;

  const items = [
    { testid: "icon-call", icon: <Phone strokeWidth={1.5} className="w-7 h-7 md:w-8 md:h-8" />, label: t.contact.phoneTitle, href: telHref, target: "_self" },
    { testid: "icon-support", icon: <Headphones strokeWidth={1.5} className="w-7 h-7 md:w-8 md:h-8" />, label: t.contact.supportTitle, href: waHref, target: "_blank" },
    { testid: "icon-email", icon: <Mail strokeWidth={1.5} className="w-7 h-7 md:w-8 md:h-8" />, label: t.contact.emailTitle, href: mailHref, target: "_self" },
  ];

  return (
    <section id="contact" data-testid="contact-section" className="bg-white py-20 md:py-28">
      <div className="mx-auto max-w-5xl px-5 md:px-10 text-center">
        <span className="inline-block text-[#0A3D42]/80 font-semibold uppercase tracking-widest text-xs">{t.contact.pre}</span>
        <h2 className="mt-2 font-display text-3xl md:text-5xl text-[#0A3D42]">{t.contact.title}</h2>
        <p className="mt-3 text-[#3a5358] max-w-xl mx-auto">{t.contact.sub}</p>

        <div className="mt-12 md:mt-16 flex items-start justify-center gap-10 sm:gap-16 md:gap-24 flex-wrap">
          {items.map((it) => (
            <a
              key={it.testid}
              data-testid={it.testid}
              href={it.href}
              target={it.target}
              rel={it.target === "_blank" ? "noopener noreferrer" : undefined}
              className="group flex flex-col items-center gap-3 text-[#0A3D42] hover:text-[#062B2F] transition-colors"
            >
              <span className="inline-flex items-center justify-center w-14 h-14 md:w-16 md:h-16 rounded-full text-[#0A3D42] transition-transform duration-300 group-hover:-translate-y-1">
                {it.icon}
              </span>
              <span className="text-xs md:text-sm font-light tracking-wide text-[#0A3D42]">{it.label}</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
