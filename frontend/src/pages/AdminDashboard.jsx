import React, { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { LogOut, Plus, Trash2, Edit3, Save, X, Upload, Inbox, Settings as SettingsIcon, FolderKanban, Image as ImageIcon, RefreshCw } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useSettings } from "../contexts/SettingsContext";
import api, { absUrl } from "../lib/api";

const MARKETS = [
  { v: "arab", l: "السوق العربي" },
  { v: "foreign", l: "السوق الأجنبي" },
];
const CATS = [
  { v: "websites", l: "مواقع إلكترونية" },
  { v: "stores", l: "متاجر رقمية" },
  { v: "other", l: "أخرى" },
];

const blankProject = { title_ar: "", title_en: "", description_ar: "", description_en: "", market: "arab", category: "websites", live_url: "", file: null };

function ProjectForm({ initial, onSave, onCancel, busy }) {
  const [form, setForm] = useState({ ...blankProject, ...initial });
  const handle = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const handleFile = (e) => setForm((f) => ({ ...f, file: e.target.files?.[0] || null }));
  return (
    <form
      className="admin-card p-6 space-y-4"
      onSubmit={(e) => { e.preventDefault(); onSave(form); }}
      data-testid="project-form"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1">اسم المشروع (عربي)</label>
          <input data-testid="project-title-ar-input" required value={form.title_ar} onChange={handle("title_ar")} className="light-input w-full" dir="rtl" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1">Project Name (English)</label>
          <input data-testid="project-title-en-input" required value={form.title_en} onChange={handle("title_en")} className="light-input w-full" dir="ltr" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1">وصف قصير (عربي)</label>
          <textarea data-testid="project-desc-ar-input" value={form.description_ar} onChange={handle("description_ar")} rows={3} className="light-input w-full resize-y" dir="rtl" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1">Short Description (English)</label>
          <textarea data-testid="project-desc-en-input" value={form.description_en} onChange={handle("description_en")} rows={3} className="light-input w-full resize-y" dir="ltr" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1">تصنيف السوق</label>
          <select data-testid="project-market-select" value={form.market} onChange={handle("market")} className="light-input w-full">
            {MARKETS.map((m) => <option key={m.v} value={m.v}>{m.l}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1">نوع المشروع</label>
          <select data-testid="project-category-select" value={form.category} onChange={handle("category")} className="light-input w-full">
            {CATS.map((c) => <option key={c.v} value={c.v}>{c.l}</option>)}
          </select>
        </div>
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1">رابط المشروع (Live URL)</label>
        <input data-testid="project-url-input" type="url" value={form.live_url} onChange={handle("live_url")} placeholder="https://..." className="light-input w-full" dir="ltr" />
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1">صورة المشروع</label>
        <input data-testid="project-file-input" type="file" accept="image/*" onChange={handleFile} className="block w-full text-sm" />
      </div>
      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} className="btn-3d btn-3d-light bg-white text-[#112325] px-5 h-11 rounded-xl font-semibold inline-flex items-center gap-2">
          <X className="w-4 h-4" />إلغاء
        </button>
        <button data-testid="project-save-btn" type="submit" disabled={busy} className="btn-3d bg-[#0A3D42] text-white px-5 h-11 rounded-xl font-semibold inline-flex items-center gap-2 disabled:opacity-60">
          <Save className="w-4 h-4" />حفظ
        </button>
      </div>
    </form>
  );
}

export default function AdminDashboard() {
  const { user, logout, checking } = useAuth();
  const { settings, refresh, logoUrl } = useSettings();
  const nav = useNavigate();
  const [tab, setTab] = useState("projects");
  const [projects, setProjects] = useState([]);
  const [leads, setLeads] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [settingsForm, setSettingsForm] = useState(null);

  useEffect(() => { setSettingsForm(settings); }, [settings]);

  const loadProjects = async () => {
    const { data } = await api.get("/projects");
    setProjects(data || []);
  };
  const loadLeads = async () => {
    const { data } = await api.get("/leads");
    setLeads(data || []);
  };

  useEffect(() => {
    if (user) { loadProjects(); loadLeads(); }
  }, [user]);

  if (checking) return <div className="admin-shell grid place-items-center"><RefreshCw className="w-6 h-6 animate-spin text-[#0A3D42]" /></div>;
  if (!user) return <Navigate to="/admin/login" replace />;

  const saveProject = async (form) => {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("title_ar", form.title_ar);
      fd.append("title_en", form.title_en);
      fd.append("description_ar", form.description_ar || "");
      fd.append("description_en", form.description_en || "");
      fd.append("market", form.market);
      fd.append("category", form.category);
      fd.append("live_url", form.live_url || "");
      if (form.file) fd.append("file", form.file);
      if (editing) {
        await api.put(`/projects/${editing.id}`, fd, { headers: { "Content-Type": "multipart/form-data" } });
        toast.success("تم تحديث المشروع");
      } else {
        await api.post("/projects", fd, { headers: { "Content-Type": "multipart/form-data" } });
        toast.success("تم إضافة المشروع");
      }
      setShowAdd(false); setEditing(null);
      await loadProjects();
    } catch (e) {
      toast.error("فشلت العملية");
    } finally { setBusy(false); }
  };

  const removeProject = async (id) => {
    if (!window.confirm("حذف المشروع؟")) return;
    await api.delete(`/projects/${id}`);
    toast.success("تم الحذف");
    await loadProjects();
  };

  const saveSettings = async () => {
    setBusy(true);
    try {
      const { agency_name, phone, whatsapp, support_phone, email } = settingsForm;
      await api.put("/settings", { agency_name, phone, whatsapp, support_phone, email });
      await refresh();
      toast.success("تم حفظ الإعدادات");
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "فشل الحفظ");
    } finally { setBusy(false); }
  };

  const uploadLogo = async (file) => {
    const fd = new FormData();
    fd.append("file", file);
    setBusy(true);
    try {
      await api.post("/settings/logo", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await refresh();
      toast.success("تم تحديث الشعار");
    } finally { setBusy(false); }
  };

  const removeLead = async (id) => {
    if (!window.confirm("حذف الطلب؟")) return;
    await api.delete(`/leads/${id}`);
    await loadLeads();
  };

  const changeLeadStatus = async (id, status) => {
    const fd = new FormData();
    fd.append("status", status);
    try {
      await api.patch(`/leads/${id}`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setLeads((prev) => prev.map((l) => (l.id === id ? { ...l, status } : l)));
      toast.success("تم تحديث الحالة");
    } catch {
      toast.error("فشل تحديث الحالة");
    }
  };

  const STATUS_LABEL = { new: "جديد", contacted: "تم التواصل", won: "تم الكسب", lost: "مفقود" };
  const STATUS_CLASS = {
    new: "bg-[#E6F2F5] text-[#0A3D42]",
    contacted: "bg-amber-50 text-amber-700",
    won: "bg-emerald-50 text-emerald-700",
    lost: "bg-rose-50 text-rose-700",
  };

  const tabs = [
    { id: "projects", label: "المشاريع", icon: <FolderKanban className="w-4 h-4" /> },
    { id: "leads", label: "الطلبات", icon: <Inbox className="w-4 h-4" /> },
    { id: "settings", label: "الإعدادات", icon: <SettingsIcon className="w-4 h-4" /> },
  ];

  return (
    <div className="admin-shell" data-testid="admin-dashboard">
      <header className="bg-white border-b border-[#EAF1F2] sticky top-0 z-30">
        <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#0A3D42] text-white grid place-items-center font-display">N</div>
            <span className="font-display text-lg text-[#112325]">لوحة التحكم</span>
          </div>
          <div className="flex items-center gap-2">
            <a href="/" className="text-sm font-semibold text-[#3a5358] hover:text-[#0A3D42]" data-testid="view-site-link">عرض الموقع</a>
            <button onClick={async () => { await logout(); nav("/admin/login"); }} data-testid="admin-logout-btn" className="btn-3d btn-3d-light bg-white text-[#112325] px-4 h-10 rounded-xl inline-flex items-center gap-2 font-semibold">
              <LogOut className="w-4 h-4" />خروج
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="seg-track mb-6" data-testid="admin-tabs">
          {tabs.map((tt) => (
            <button key={tt.id} data-testid={`tab-${tt.id}`} className="seg-btn inline-flex items-center gap-2" data-active={tab === tt.id} onClick={() => setTab(tt.id)}>
              {tt.icon}{tt.label}
            </button>
          ))}
        </div>

        {tab === "projects" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl">المشاريع ({projects.length})</h2>
              <button onClick={() => { setEditing(null); setShowAdd(true); }} data-testid="add-project-btn" className="btn-3d bg-[#0A3D42] text-white px-5 h-11 rounded-xl font-semibold inline-flex items-center gap-2">
                <Plus className="w-4 h-4" />مشروع جديد
              </button>
            </div>

            {(showAdd || editing) && (
              <ProjectForm
                initial={editing || blankProject}
                busy={busy}
                onCancel={() => { setShowAdd(false); setEditing(null); }}
                onSave={saveProject}
              />
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {projects.map((p) => (
                <div key={p.id} className="admin-card overflow-hidden" data-testid={`admin-project-${p.id}`}>
                  <div className="aspect-[16/10] bg-[#F1F6F7] overflow-hidden">
                    {p.image_url ? <img src={p.image_url.startsWith("http") ? p.image_url : absUrl(p.image_url)} alt={p.title_ar || p.title} className="w-full h-full object-cover" /> : <div className="w-full h-full grid place-items-center text-[#3a5358]"><ImageIcon className="w-8 h-8" /></div>}
                  </div>
                  <div className="p-4">
                    <div className="font-semibold text-[#112325]">{p.title_ar || p.title}</div>
                    <div className="text-xs text-[#3a5358]" dir="ltr">{p.title_en}</div>
                    <div className="text-xs text-[#3a5358] mt-1">{p.market} / {p.category}</div>
                    {p.live_url && <a href={p.live_url} target="_blank" rel="noreferrer" className="text-xs text-[#0A3D42] underline mt-1 inline-block" dir="ltr">{p.live_url}</a>}
                    <div className="mt-3 flex gap-2">
                      <button onClick={() => { setShowAdd(false); setEditing(p); }} className="btn-3d btn-3d-light bg-white text-[#112325] px-3 h-9 rounded-lg text-sm inline-flex items-center gap-1"><Edit3 className="w-3.5 h-3.5" />تعديل</button>
                      <button data-testid={`delete-project-${p.id}`} onClick={() => removeProject(p.id)} className="btn-3d btn-3d-light bg-white text-red-600 px-3 h-9 rounded-lg text-sm inline-flex items-center gap-1"><Trash2 className="w-3.5 h-3.5" />حذف</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "leads" && (
          <div className="admin-card overflow-hidden" data-testid="leads-table">
            <table className="w-full text-right">
              <thead className="bg-[#F1F6F7] text-[#3a5358] text-sm">
                <tr>
                  <th className="p-3">الاسم</th>
                  <th className="p-3">البريد</th>
                  <th className="p-3">الهاتف</th>
                  <th className="p-3">الخدمة</th>
                  <th className="p-3">الرسالة</th>
                  <th className="p-3">الحالة</th>
                  <th className="p-3">التاريخ</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {leads.length === 0 && (
                  <tr><td colSpan={8} className="p-8 text-center text-[#3a5358]">لا توجد طلبات حتى الآن</td></tr>
                )}
                {leads.map((l) => (
                  <tr key={l.id} className="border-t border-[#EAF1F2]" data-testid={`lead-row-${l.id}`}>
                    <td className="p-3 font-semibold">{l.name}</td>
                    <td className="p-3" dir="ltr">{l.email}</td>
                    <td className="p-3" dir="ltr">{l.phone || "-"}</td>
                    <td className="p-3">{l.service}</td>
                    <td className="p-3 max-w-xs truncate" title={l.message}>{l.message}</td>
                    <td className="p-3">
                      <div className="flex flex-col gap-1">
                        <span className={`inline-block w-fit px-2 py-1 rounded-md text-xs font-semibold ${STATUS_CLASS[l.status] || STATUS_CLASS.new}`} data-testid={`lead-status-badge-${l.id}`}>
                          {STATUS_LABEL[l.status] || l.status}
                        </span>
                        <select
                          data-testid={`lead-status-select-${l.id}`}
                          value={l.status || "new"}
                          onChange={(e) => changeLeadStatus(l.id, e.target.value)}
                          className="light-input text-xs py-1 px-2"
                        >
                          <option value="new">جديد</option>
                          <option value="contacted">تم التواصل</option>
                          <option value="won">تم الكسب</option>
                          <option value="lost">مفقود</option>
                        </select>
                      </div>
                    </td>
                    <td className="p-3 text-xs text-[#3a5358]" dir="ltr">{new Date(l.created_at).toLocaleString()}</td>
                    <td className="p-3"><button onClick={() => removeLead(l.id)} data-testid={`lead-delete-${l.id}`} className="text-red-600 hover:underline text-sm">حذف</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "settings" && settingsForm && (
          <div className="admin-card p-6 max-w-2xl space-y-4">
            <h2 className="font-display text-2xl mb-2">إعدادات الموقع</h2>
            <div>
              <label className="block text-sm font-semibold mb-1">شعار/اسم الوكالة</label>
              <input data-testid="agency-name-input" value={settingsForm.agency_name || ""} onChange={(e) => setSettingsForm({ ...settingsForm, agency_name: e.target.value })} className="light-input w-full" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">صورة الشعار</label>
              <div className="flex items-center gap-4">
                {logoUrl ? <img src={logoUrl} alt="logo" className="h-12" /> : <div className="h-12 w-12 rounded-xl bg-[#F1F6F7] grid place-items-center text-[#3a5358]"><ImageIcon className="w-5 h-5" /></div>}
                <label className="btn-3d btn-3d-light bg-white text-[#112325] px-4 h-10 rounded-xl font-semibold inline-flex items-center gap-2 cursor-pointer">
                  <Upload className="w-4 h-4" />رفع شعار
                  <input data-testid="logo-upload-input" type="file" accept="image/*" hidden onChange={(e) => e.target.files?.[0] && uploadLogo(e.target.files[0])} />
                </label>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1">رقم الهاتف</label>
                <input data-testid="phone-input" value={settingsForm.phone || ""} onChange={(e) => setSettingsForm({ ...settingsForm, phone: e.target.value })} className="light-input w-full" dir="ltr" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">واتساب (أرقام فقط)</label>
                <input data-testid="whatsapp-input" value={settingsForm.whatsapp || ""} onChange={(e) => setSettingsForm({ ...settingsForm, whatsapp: e.target.value })} className="light-input w-full" dir="ltr" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">رقم الدعم الفني</label>
                <input data-testid="support-phone-input" value={settingsForm.support_phone || ""} onChange={(e) => setSettingsForm({ ...settingsForm, support_phone: e.target.value })} className="light-input w-full" dir="ltr" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">البريد الإلكتروني</label>
                <input data-testid="email-input" type="email" value={settingsForm.email || ""} onChange={(e) => setSettingsForm({ ...settingsForm, email: e.target.value })} className="light-input w-full" dir="ltr" />
              </div>
            </div>
            <div className="flex justify-end">
              <button data-testid="save-settings-btn" onClick={saveSettings} disabled={busy} className="btn-3d bg-[#0A3D42] text-white px-5 h-11 rounded-xl font-semibold inline-flex items-center gap-2 disabled:opacity-60"><Save className="w-4 h-4" />حفظ الإعدادات</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
