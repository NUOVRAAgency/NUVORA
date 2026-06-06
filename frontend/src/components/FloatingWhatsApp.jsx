import React from "react";
import { useSettings } from "../contexts/SettingsContext";

export default function FloatingWhatsApp() {
  const { settings } = useSettings();
  const phone = (settings.whatsapp || settings.phone || "").replace(/[^\d]/g, "");
  const href = phone ? `https://wa.me/${phone}` : "#";
  return (
    <a
      data-testid="floating-whatsapp"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="WhatsApp"
      className="fab-wa"
    >
      <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true">
        <path d="M20.52 3.48A11.93 11.93 0 0012.06 0C5.5 0 .14 5.34.14 11.9c0 2.1.55 4.14 1.6 5.94L0 24l6.32-1.66a11.86 11.86 0 005.73 1.46h.01c6.56 0 11.92-5.34 11.92-11.9 0-3.18-1.24-6.17-3.46-8.42zM12.06 21.5h-.01a9.6 9.6 0 01-4.9-1.34l-.35-.21-3.75.98 1-3.66-.23-.37a9.51 9.51 0 01-1.47-5.1c0-5.27 4.31-9.56 9.7-9.56 2.6 0 5.04 1.01 6.88 2.85a9.5 9.5 0 012.82 6.74c0 5.27-4.31 9.67-9.69 9.67zm5.55-7.13c-.3-.15-1.79-.88-2.07-.98-.28-.1-.48-.15-.69.15s-.79.98-.97 1.18c-.18.2-.36.22-.66.07-.3-.15-1.27-.46-2.42-1.49a9.16 9.16 0 01-1.69-2.09c-.18-.3-.02-.46.13-.61.13-.13.3-.36.45-.54.15-.18.2-.3.3-.5.1-.2.05-.38-.02-.53-.07-.15-.69-1.66-.95-2.27-.25-.6-.5-.51-.69-.52h-.59c-.2 0-.53.08-.81.38-.28.3-1.06 1.03-1.06 2.51 0 1.48 1.08 2.91 1.23 3.11.15.2 2.13 3.25 5.17 4.55.72.31 1.28.5 1.71.64.72.23 1.37.2 1.89.12.58-.09 1.79-.73 2.04-1.43.25-.7.25-1.3.18-1.43-.07-.13-.27-.2-.57-.36z"/>
      </svg>
    </a>
  );
}
