import React, { useEffect } from "react";
import { X } from "lucide-react";
import { useLang } from "../contexts/LangContext";

const links = [
  { id: "home", to: "#home", testid: "drawer-link-home", key: "home" },
  { id: "work", to: "#work", testid: "drawer-link-work", key: "work" },
  { id: "consult", to: "#consult", testid: "drawer-link-consult", key: "consult" },
  { id: "contact", to: "#contact", testid: "drawer-link-contact", key: "contact" },
];

export default function DrawerMenu({ open, onClose }) {
  const { t, dir } = useLang();

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  const sideClass = dir === "rtl" ? "right-0 border-l" : "left-0 border-r";
  const slideStart = dir === "rtl" ? "translate-x-full" : "-translate-x-full";

  return (
    <div className={`fixed inset-0 z-[60] ${open ? "pointer-events-auto" : "pointer-events-none"}`} aria-hidden={!open}>
      <div
        onClick={onClose}
        className={`absolute inset-0 bg-[#0A3D42]/40 backdrop-blur-sm transition-opacity duration-300 ${open ? "opacity-100" : "opacity-0"}`}
      />
      <aside
        data-testid="drawer-panel"
        className={`absolute top-0 ${sideClass} h-full w-[86%] max-w-sm bg-white border-[#E0EBED] shadow-2xl transition-transform duration-500 ease-[cubic-bezier(.2,.7,.2,1)] ${open ? "translate-x-0" : slideStart}`}
      >
        <div className="flex items-center justify-between px-6 h-20 border-b border-[#EAF1F2]">
          <span className="font-display text-2xl text-[#112325]">NUVORA</span>
          <button
            data-testid="drawer-close-btn"
            onClick={onClose}
            className="w-10 h-10 rounded-xl inline-flex items-center justify-center bg-[#F1F6F7] text-[#112325] hover:bg-[#E6F2F5] transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="p-6 flex flex-col gap-2">
          {links.map((l, i) => (
            <a
              key={l.id}
              href={l.to}
              onClick={onClose}
              data-testid={l.testid}
              className="block px-4 py-4 rounded-xl text-lg font-semibold text-[#112325] hover:bg-[#F1F6F7] hover:text-[#0A3D42] transition-colors"
              style={{ transitionDelay: open ? `${i * 40}ms` : "0ms" }}
            >
              {t.nav[l.key]}
            </a>
          ))}
        </nav>
      </aside>
    </div>
  );
}
