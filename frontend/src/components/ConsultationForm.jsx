import React, { useState } from "react";
import { Send } from "lucide-react";
import { toast } from "sonner";
import api from "../lib/api";
import { useLang } from "../contexts/LangContext";

export default function ConsultationForm() {
  const { t } = useLang();
  const [form, setForm] = useState({ name: "", email: "", phone: "", service: t.form.services[0], message: "" });
  const [submitting, setSubmitting] = useState(false);

  const onChange = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) {
      toast.error(t.form.title);
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/leads", form);
      toast.success(t.form.success);
      setForm({ name: "", email: "", phone: "", service: t.form.services[0], message: "" });
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t.form.title);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section id="consult" data-testid="consult-section" className="bg-[#F6FAFB] py-20 md:py-28 border-t border-b border-[#EAF1F2]">
      <div className="mx-auto max-w-3xl px-5 md:px-10">
        <div className="text-center">
          <h2 data-testid="consult-title" className="font-display text-3xl md:text-5xl text-[#0A3D42]">{t.form.title}</h2>
          <p className="mt-3 text-[#3a5358]">{t.form.sub}</p>
        </div>
        <form onSubmit={submit} className="mt-10 admin-card p-6 md:p-8 space-y-4" data-testid="consult-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input data-testid="consult-name" required value={form.name} onChange={onChange("name")} placeholder={t.form.name} className="light-input w-full" />
            <input data-testid="consult-email" type="email" required value={form.email} onChange={onChange("email")} placeholder={t.form.email} className="light-input w-full" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input data-testid="consult-phone" value={form.phone} onChange={onChange("phone")} placeholder={t.form.phone} className="light-input w-full" />
            <select data-testid="consult-service" value={form.service} onChange={onChange("service")} className="light-input w-full">
              {t.form.services.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <textarea data-testid="consult-message" required value={form.message} onChange={onChange("message")} placeholder={t.form.details} rows={5} className="light-input w-full resize-y" />
          <div className="flex justify-end">
            <button data-testid="consult-submit" type="submit" disabled={submitting} className="btn-3d bg-[#0A3D42] hover:bg-[#0d4a50] text-white px-7 h-12 rounded-xl font-bold inline-flex items-center gap-2 disabled:opacity-60">
              <Send className="w-4 h-4 rtl:-scale-x-100" />
              <span>{submitting ? "..." : t.form.submit}</span>
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
