import React from "react";
import { Phone, HeadphonesIcon, Mail } from "lucide-react";
import { useLang } from "../contexts/LangContext";
import { useSettings } from "../contexts/SettingsContext";

export default function Contact() {
  const { t } = useLang();
  const { settings } = useSettings();

  const cards = [
    {
      testid: "contact-card-phone",
      icon: <Phone className="w-7 h-7" />,
      title: t.contact.phoneTitle,
      main: settings.phone,
      cta: t.contact.phoneCta,
      href: `tel:${(settings.phone || "").replace(/[^\d+]/g, "")}`,
    },
    {
      testid: "contact-card-support",
      icon: <HeadphonesIcon className="w-7 h-7" />,
      title: t.contact.supportTitle,
      main: settings.support_phone,
      cta: t.contact.supportCta,
      href: `tel:${(settings.support_phone || "").replace(/[^\d+]/g, "")}`,
    },
    {
      testid: "contact-card-email",
      icon: <Mail className="w-7 h-7" />,
      title: t.contact.emailTitle,
      main: settings.email,
      cta: t.contact.emailCta,
      href: `mailto:${settings.email}`,
    },
  ];

  return (
    <section id="contact" data-testid="contact-section" className="bg-white py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-5 md:px-10">
        <div className="text-center max-w-2xl mx-auto">
          <span className="inline-block text-[#0A3D42]/80 font-semibold uppercase tracking-widest text-xs">{t.contact.pre}</span>
          <h2 className="mt-2 font-display text-3xl md:text-5xl text-[#0A3D42]">{t.contact.title}</h2>
          <p className="mt-3 text-[#3a5358]">{t.contact.sub}</p>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {cards.map((c) => (
            <a
              key={c.testid}
              data-testid={c.testid}
              href={c.href}
              className="proj-card p-7 block group"
            >
              <div className="w-14 h-14 rounded-2xl bg-[#E6F2F5] text-[#0A3D42] inline-flex items-center justify-center mb-5 group-hover:bg-[#0A3D42] group-hover:text-white transition-colors">
                {c.icon}
              </div>
              <div className="text-sm text-[#3a5358] font-semibold">{c.title}</div>
              <div className="mt-1 font-display text-2xl text-[#112325] break-all" dir="ltr">{c.main}</div>
              <div className="mt-4 inline-flex items-center gap-2 text-[#0A3D42] font-semibold">
                {c.cta}
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
